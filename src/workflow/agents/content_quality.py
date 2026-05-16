import json
import re
from dataclasses import asdict
from typing import Any, Dict, List

from src.ingestion.compact_context import ensure_compact_context, render_compact_context
from src.models.context import DocumentContext
from src.models.slide import Slide, SlideContent
from src.utils.llm import chat
from src.utils.parse_llm_response import parse_json_response


class ContentQualityAgent:
    MAX_OUTPUT_TOKENS = 2048
    MAX_EVIDENCE_PER_SLIDE = 1800
    BATCH_SIZE = 3
    BAD_PATTERNS = [
        r"source-backed details required",
        r"\bdetails required\b",
        r"\bplaceholder\b",
        r"\btodo\b",
        r"\bn/?a\b",
        r"insufficient source",
        r"not enough information",
        r"dagon university research journal",
        r"preserving the deci",
        r"explain the .* preserving",
        r"^#+\s",
        r"\s#+\s",
    ]

    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list) -> str:
        return chat(self.model, messages, temperature=0.2, max_tokens=self.MAX_OUTPUT_TOKENS)

    def repair(self, slides: List[SlideContent], slide_specs: List[Slide], context: DocumentContext, slide_packets: List[Dict[str, Any]] | None = None) -> List[SlideContent]:
        packet_by_number = {int(packet.get("slide_number")): packet for packet in (slide_packets or []) if packet.get("slide_number") is not None}
        issues, evidence_by_number, soft_issues = self._detect_all_issues(slides, context, packet_by_number)
        if not issues:
            if soft_issues:
                print(f"[ContentQA] No blocking content issues found. Soft warnings on {len(soft_issues)} slide(s).")
            else:
                print("[ContentQA] No blocking content issues found.")
            return slides
        print(f"[ContentQA] Repairing {len(issues)} slide(s): {sorted(issues)}")
        repaired_by_number: Dict[int, Any] = {}
        flagged = [slide for slide in slides if slide.slide.slide_number in issues]
        for batch in self._chunks(flagged, self.BATCH_SIZE):
            repaired_by_number.update(self._repair_batch(batch, slide_specs, context, issues, evidence_by_number, packet_by_number))
        repaired_slides = []
        for slide in slides:
            content = repaired_by_number.get(slide.slide.slide_number, slide.content)
            content = self._normalise_content(content, slide.content)
            repaired_slides.append(SlideContent(slide=slide.slide, content=content))
        unresolved, _, _ = self._detect_all_issues(repaired_slides, context, packet_by_number)
        if unresolved:
            repaired_slides = self._apply_deterministic_fallbacks(repaired_slides, unresolved, evidence_by_number, packet_by_number)
            unresolved, _, _ = self._detect_all_issues(repaired_slides, context, packet_by_number)
        if unresolved:
            raise RuntimeError(f"Content QA could not repair blocking slide issues: {unresolved}")
        return repaired_slides

    def _repair_batch(
        self,
        slides: List[SlideContent],
        slide_specs: List[Slide],
        context: DocumentContext,
        issues: Dict[int, List[str]],
        evidence_by_number: Dict[int, str],
        packet_by_number: Dict[int, Dict[str, Any]],
    ) -> Dict[int, Any]:
        spec_by_number = {spec.slide_number: spec for spec in slide_specs}
        payload = []
        repaired: Dict[int, Any] = {}
        for slide in slides:
            packet = packet_by_number.get(slide.slide.slide_number)
            evidence = evidence_by_number.get(slide.slide.slide_number) or self._packet_evidence(packet) or self._retrieve_evidence(context, slide)
            deterministic = self._deterministic_content(slide, evidence, packet)
            if deterministic:
                repaired[slide.slide.slide_number] = deterministic
                continue
            spec = spec_by_number.get(slide.slide.slide_number, slide.slide)
            spec_data = asdict(spec)
            if hasattr(spec_data.get("slide_type"), "value"):
                spec_data["slide_type"] = spec_data["slide_type"].value
            payload.append(
                {
                    "slide_number": slide.slide.slide_number,
                    "slide_title": slide.slide.slide_title,
                    "slide_spec": spec_data,
                    "current_content": slide.content,
                    "detected_issues": issues.get(slide.slide.slide_number, []),
                    "required_checks": (packet or {}).get("required_checks", []),
                    "required_facts": (packet or {}).get("required_facts", []),
                    "source_evidence": evidence,
                }
            )
        if not payload:
            return repaired
        prompt = (
            "# ROLE\n"
            "You are a strict lecture content QA editor.\n\n"
            "# TASK\n"
            "Rewrite only the flagged slide contents so each slide is faithful to its source evidence, matches its title, and is ready for oral presentation.\n\n"
            "# RULES\n"
            "- Return 3 to 5 concise bullet phrases per slide.\n"
            "- Remove all placeholders and vague filler.\n"
            "- Stay within the slide title and goal.\n"
            "- Preserve concrete formulas, variables, numbers, software names, and interpretation points from the evidence.\n"
            "- Do not invent facts outside the evidence.\n"
            "- Do not copy source markdown headings, page headers, journal headers, or figure labels as bullets.\n"
            "- For slack/result slides, include the numerical result and its meaning when evidence provides it.\n"
            "- For objective slides, include the objective formula when evidence provides it.\n"
            "- For constraint slides, include the constraint inequalities when evidence provides them.\n"
            "- For software slides, name the tool and source workflow actions.\n\n"
            "# FLAGGED SLIDES\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
            "# OUTPUT\n"
            "Return ONLY valid JSON array:\n"
            '[{"slide_number": 1, "content": ["bullet 1", "bullet 2", "bullet 3"]}]'
        )
        raw = self._chat([{"role": "user", "content": prompt}])
        invoke_fn = lambda msgs: type("R", (), {"content": self._chat(msgs)})()
        data = parse_json_response(raw, invoke_fn, expect_list=True)
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                number = item.get("slide_number")
                if number is None:
                    continue
                repaired[int(number)] = item.get("content", [])
        for slide in slides:
            if slide.slide.slide_number not in repaired:
                packet = packet_by_number.get(slide.slide.slide_number)
                repaired[slide.slide.slide_number] = self._fallback_content(
                    slide,
                    evidence_by_number.get(slide.slide.slide_number) or self._packet_evidence(packet) or self._retrieve_evidence(context, slide),
                    packet,
                )
        return repaired

    def _retrieve_evidence(self, context: DocumentContext, slide: SlideContent) -> str:
        evidence = self._lexical_evidence(context, slide)
        if not evidence.strip():
            compact = ensure_compact_context(context)
            evidence = render_compact_context(compact, max_chars=self.MAX_EVIDENCE_PER_SLIDE)
        return evidence[: self.MAX_EVIDENCE_PER_SLIDE]

    def _lexical_evidence(self, context: DocumentContext, slide: SlideContent) -> str:
        pages = self._split_pages(context.text_content.markdown)
        if not pages:
            return ""
        query = f"{slide.slide.slide_title} {slide.slide.goal}"
        query_l = query.lower()
        terms = self._query_terms(query_l)
        boosters = self._topic_boosters(query_l)
        must_terms = self._must_terms(query_l)
        scored = []
        for page_num, page_text in pages:
            text_l = page_text.lower()
            score = 0
            for term in terms:
                score += text_l.count(term)
            for term, weight in boosters.items():
                if term in text_l:
                    score += weight
            for term in must_terms:
                if term in text_l:
                    score += 15
            if "product mix" in query_l and "product mix" in text_l:
                score += 250
            if any(word in query_l for word in ["formulat", "model"]) and ("$$" in page_text or "\\le" in page_text or "<=" in page_text):
                score += 50
            if "objective" in query_l and re.search(r"\b[A-Za-z]\s*=\s*[^.\n]+", page_text):
                score += 30
            if any(word in query_l for word in ["optimal", "result", "solution value"]):
                if re.search(r"\b[A-Za-z]\s*_?\s*\d*\s*=\s*-?\d+(?:\.\d+)?", page_text):
                    score += 90
                if re.search(r"(maximum|minimum|profit|income)[^.\d$]{0,80}\$?\s*\d+", page_text, flags=re.IGNORECASE):
                    score += 50
            if "slack" in query_l and re.search(r"(slack|not used|unused|remaining)[^.\d]{0,80}\d+", page_text, flags=re.IGNORECASE):
                score += 90
            if score > 0:
                clean = re.sub(r"\s+", " ", page_text).strip()
                scored.append((score, page_num, clean))
        if not scored:
            return ""
        scored.sort(key=lambda item: (-item[0], item[1]))
        page_lookup = {page_num: page_text for page_num, page_text in pages}
        selected = []
        for score, page_num, text in scored[:2]:
            selected.append((score, page_num, text))
            if any(word in query_l for word in ["formulat", "model", "problem"]):
                neighbor = page_lookup.get(page_num + 1)
                if neighbor:
                    neighbor_score = score - 1
                    if "$$" in neighbor or "\\le" in neighbor or "<=" in neighbor:
                        neighbor_score = score + 30
                    selected.append((neighbor_score, page_num + 1, re.sub(r"\s+", " ", neighbor).strip()))
        selected.sort(key=lambda item: (-item[0], item[1]))
        blocks = []
        seen_pages = set()
        for score, page_num, text in selected[:3]:
            if page_num in seen_pages:
                continue
            seen_pages.add(page_num)
            blocks.append(f"--- Page {page_num} evidence ---\n{text[:1200]}")
        return "\n\n".join(blocks)

    @staticmethod
    def _split_pages(markdown: str) -> List[tuple[int, str]]:
        matches = list(re.finditer(r"<!--\s*PAGE\s+(\d+)\s*-->", markdown, flags=re.IGNORECASE))
        if not matches:
            return [(1, markdown)]
        pages = []
        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
            pages.append((int(match.group(1)), markdown[start:end].strip()))
        return pages

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        stop = {
            "explain", "preserving", "source", "slide", "concrete", "facts", "title", "goal",
            "with", "from", "that", "this", "into", "using", "method", "solution", "values",
            "linear", "programming",
        }
        terms = []
        for term in re.findall(r"[a-z0-9_]+", query):
            if len(term) >= 4 and term not in stop:
                terms.append(term)
        return terms[:18]

    @staticmethod
    def _topic_boosters(query: str) -> Dict[str, int]:
        boosters: Dict[str, int] = {}
        if "objective" in query:
            boosters.update({"objective": 8, "maximize": 6, "minimize": 6, "profit": 4, "income": 4, " z ": 3})
        if "constraint" in query:
            boosters.update({"<=": 8, "\\le": 8, "constraint": 8, "subject to": 6, "available": 3})
        if "optimal" in query or "result" in query or "solution value" in query:
            boosters.update({"optimal": 8, "maximum": 5, "minimum": 5, "profit": 4, "income": 4, " = ": 3})
        if "slack" in query:
            boosters.update({"slack": 10, "not used": 6, "unused": 6, "remaining": 5, "binding": 4})
        if "software" in query or "prolp" in query:
            boosters.update({"software": 8, "input": 5, "entry data": 6, "solve": 6, "save": 5, "print": 5})
        if "graph" in query or "feasible" in query:
            boosters.update({"feasible region": 10, "straight line": 5, "boundary": 4})
        return boosters

    @staticmethod
    def _must_terms(query: str) -> List[str]:
        if "slack" in query:
            return ["slack", "not used", "unused", "remaining"]
        if "objective" in query:
            return ["objective", "maximize", "minimize"]
        if "constraint" in query:
            return ["subject to", "constraint", "<=", "\\le"]
        if "optimal" in query or "result" in query or "solution value" in query:
            return ["optimal", "maximum", "minimum", "income", "profit"]
        if "software" in query or "prolp" in query:
            return ["software", "input", "solve"]
        return []

    def _detect_issues(self, slides: List[SlideContent]) -> tuple[Dict[int, List[str]], Dict[int, List[str]]]:
        issues: Dict[int, List[str]] = {}
        soft_issues: Dict[int, List[str]] = {}
        for slide in slides:
            text = self._flatten(slide.content)
            blocking = []
            soft = []
            if self._bullet_count(slide.content) < 3:
                blocking.append("fewer than 3 usable bullets")
            if not text.strip():
                blocking.append("empty content")
            lower_text = text.lower()
            for pattern in self.BAD_PATTERNS:
                if re.search(pattern, lower_text):
                    blocking.append("placeholder or unresolved source note")
                    break
            if self._has_unbalanced_math(text):
                blocking.append("unbalanced inline math delimiter")
            if self._has_noisy_slack_values(text):
                blocking.append("unsupported slack value list")
            missing = self._missing_title_anchors(slide.slide.slide_title, lower_text)
            if missing:
                soft.append(f"title-content mismatch: missing {', '.join(missing)}")
            if blocking:
                issues[slide.slide.slide_number] = blocking
            if soft:
                soft_issues[slide.slide.slide_number] = soft
        return issues, soft_issues

    def _detect_all_issues(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
        packet_by_number: Dict[int, Dict[str, Any]] | None = None,
    ) -> tuple[Dict[int, List[str]], Dict[int, str], Dict[int, List[str]]]:
        issues, soft_issues = self._detect_issues(slides)
        evidence_by_number: Dict[int, str] = {}
        packet_by_number = packet_by_number or {}
        for slide in slides:
            packet = packet_by_number.get(slide.slide.slide_number)
            evidence = self._packet_evidence(packet) if packet else self._retrieve_evidence(context, slide)
            evidence_by_number[slide.slide.slide_number] = evidence
            evidence_issues = self._packet_contract_issues(slide, packet, evidence) if packet else self._evidence_required_issues(slide, evidence)
            if evidence_issues:
                issues.setdefault(slide.slide.slide_number, []).extend(evidence_issues)
        return issues, evidence_by_number, soft_issues

    @staticmethod
    def _packet_evidence(packet: Dict[str, Any] | None) -> str:
        if not packet:
            return ""
        pieces = []
        facts = packet.get("required_facts") or []
        if facts:
            pieces.append("Required facts:\n" + "\n".join(str(fact) for fact in facts))
        checks = packet.get("required_checks") or []
        if checks:
            pieces.append("Required checks:\n" + json.dumps(checks, ensure_ascii=False, indent=2))
        evidence = packet.get("evidence")
        if evidence:
            pieces.append(str(evidence))
        return "\n\n".join(pieces)

    def _packet_contract_issues(self, slide: SlideContent, packet: Dict[str, Any] | None, evidence: str) -> List[str]:
        if not packet:
            return self._evidence_required_issues(slide, evidence)
        content_l = self._normalise_for_match(self._flatten(slide.content))
        issues = []
        checks = packet.get("required_checks") or []
        required_facts = [fact for fact in packet.get("required_facts", []) if isinstance(fact, str)]
        if not checks and required_facts:
            checks = [{"kind": "required_facts", "items": required_facts[:6]}]
        for check in checks:
            if not isinstance(check, dict):
                continue
            kind = str(check.get("kind") or "").strip().lower()
            if kind == "objective_formula":
                formula = str(check.get("formula") or "").strip()
                if formula and not self._contains_formula(content_l, formula):
                    issues.append("missing required objective formula")
            elif kind == "constraints":
                items = [str(item) for item in check.get("items", []) if str(item).strip()]
                if items and not self._contains_enough_constraints(content_l, items):
                    issues.append("missing required constraint inequalities")
            elif kind == "result_values":
                items = [str(item) for item in check.get("items", []) if str(item).strip()]
                if items and not self._contains_values(content_l, items):
                    issues.append("missing required result values")
            elif kind == "slack_facts":
                values = self._clean_slack_values([str(item) for item in check.get("values", []) if str(item).strip()])
                sentences = [str(item) for item in check.get("sentences", []) if str(item).strip()]
                if values and not self._contains_values(content_l, values):
                    issues.append("missing required slack values")
                if sentences and not any(self._sentence_overlap(content_l, sentence) for sentence in sentences):
                    issues.append("missing required slack interpretation")
            elif kind == "workflow_actions":
                items = [str(item) for item in check.get("items", []) if str(item).strip()]
                if items:
                    action_hits = sum(1 for action in items if any(token in content_l for token in self._action_tokens(action)))
                    if action_hits < min(2, len(items)):
                        issues.append("missing required workflow actions")
            elif kind == "required_facts":
                items = [str(item) for item in check.get("items", []) if str(item).strip()]
                fact_hits = sum(1 for fact in items if self._fact_supported_in_content(content_l, fact))
                if fact_hits < min(2, len(items)):
                    issues.append("missing required packet facts")
        return list(dict.fromkeys(issues))

    def _evidence_required_issues(self, slide: SlideContent, evidence: str) -> List[str]:
        title_l = slide.slide.slide_title.lower()
        content_l = self._normalise_for_match(self._flatten(slide.content))
        evidence_l = self._normalise_for_match(evidence)
        issues = []
        evidence_objective = self._extract_objective_formula(evidence)
        if "objective" in title_l and evidence_objective:
            if not self._contains_formula(content_l, evidence_objective):
                issues.append("missing source objective formula")
        evidence_constraints = self._extract_constraints(evidence)
        if "constraint" in title_l and evidence_constraints:
            if not self._contains_enough_constraints(content_l, evidence_constraints):
                issues.append("missing source constraint inequalities")
        evidence_values = self._extract_result_values(evidence)
        if ("optimal" in title_l or "result" in title_l or "solution value" in title_l) and evidence_values:
            if not self._contains_values(content_l, evidence_values):
                issues.append("missing source optimal values")
        evidence_slack = self._extract_slack_facts(evidence)
        if ("slack" in title_l or "binding" in title_l) and evidence_slack:
            if not self._contains_values(content_l, evidence_slack["values"]) or "slack" not in content_l:
                issues.append("missing slack value and interpretation")
        evidence_actions = self._extract_software_actions(evidence)
        required_actions = self._extract_required_workflow_actions(evidence)
        if required_actions:
            evidence_actions = required_actions
        if ("software" in title_l or "prolp" in title_l or "input" in title_l or "saving" in title_l or required_actions) and evidence_actions:
            action_hits = sum(1 for action in evidence_actions if any(token in content_l for token in self._action_tokens(action)))
            if action_hits < min(2, len(evidence_actions)):
                issues.append("missing software workflow actions")
        return issues

    @staticmethod
    def _normalise_for_match(text: str) -> str:
        text = text.lower()
        text = text.replace("≤", "<=").replace("\\leq", "<=").replace("\\le", "<=")
        text = re.sub(r"\s+", " ", text)
        text = text.replace("_", "")
        return text

    @classmethod
    def _extract_objective_formula(cls, evidence: str) -> str:
        formulas = cls._extract_formulas(evidence)
        for formula in formulas:
            normal = cls._normalise_for_match(formula)
            if re.search(r"\b[a-z]\s*=", normal) and any(word in cls._normalise_for_match(evidence) for word in ["objective", "maximize", "minimize", "profit", "income"]):
                return formula
        match = re.search(r"(?:maximize|minimize|maximise|minimise|objective[^.:]*[:.]?)\s*([A-Za-z]\s*=\s*[^.\n;]+)", evidence, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @classmethod
    def _extract_constraints(cls, evidence: str) -> List[str]:
        formulas = cls._extract_formulas(evidence)
        constraints = []
        for formula in formulas:
            normal = cls._normalise_for_match(formula)
            if ("<=" in normal or ">=" in normal or " less than or equal " in normal or " greater than or equal " in normal) and re.search(r"[A-Za-z]\s*_?\s*\d+", formula):
                constraints.append(formula)
        inline = re.findall(r"([A-Za-z0-9_{}\\^+\-*/().\s]+\s*(?:<=|>=|≤|≥|\\leq?|\\geq?)\s*[A-Za-z0-9_{}\\^+\-*/().\s]+)", evidence)
        for item in inline:
            clean = re.sub(r"\s+", " ", item).strip(" .;:")
            if 4 <= len(clean) <= 120 and re.search(r"[A-Za-z]\s*_?\s*\d+", clean) and re.search(r"(<=|>=|≤|≥|\\leq?|\\geq?)", clean) and clean not in constraints:
                constraints.append(clean)
        return constraints[:5]

    @classmethod
    def _extract_result_values(cls, evidence: str) -> List[str]:
        values = []
        result_region = cls._sentences_matching(cls._clean_evidence_text(evidence), ["optimal", "maximum", "minimum", "profit", "income", "solution"])
        required_match = re.search(r"Result values:\s*([^\n.]+)", evidence, flags=re.IGNORECASE)
        if required_match:
            required_values = required_match.group(1)
            result_region.append(required_values)
            without_assignments = re.sub(r"\b[A-Za-z]\s*_?\s*\d*\s*=\s*-?\d+(?:\.\d+)?\b", " ", required_values)
            for match in re.findall(r"\b\d+(?:\.\d+)?\b", without_assignments):
                clean = re.sub(r"\s+", "", match)
                if clean and clean not in values:
                    values.append(clean)
        for text in result_region:
            for match in re.findall(r"\b[A-Za-z]\s*_?\s*\d*\s*=\s*-?\d+(?:\.\d+)?\b", text):
                clean = re.sub(r"\s+", "", match.replace("$", ""))
                if clean and clean not in values:
                    values.append(clean)
            for match in re.findall(r"(?:maximum|minimum|profit|income|objective value)[^.\d$]{0,60}\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE):
                raw = next((part for part in match if part), "")
                clean = re.sub(r"\s+", "", raw.replace("$", ""))
                if clean and clean not in values:
                    values.append(clean)
        return values[:6]

    @classmethod
    def _extract_slack_facts(cls, evidence: str) -> Dict[str, List[str]]:
        required_match = re.search(r"Slack values?:\s*([^\n.]+)", evidence, flags=re.IGNORECASE)
        if required_match:
            values = []
            for match in re.findall(r"\b\d+(?:\.\d+)?\s*(?:ft\^?2|ft\$?\^?2|lb|hours?|units?|%)?|\$?\b\d+(?:\.\d+)?\b", required_match.group(1), flags=re.IGNORECASE):
                clean = re.sub(r"\s+", " ", match.replace("$", "")).strip()
                if clean and clean not in values:
                    values.append(clean)
            values = cls._clean_slack_values(values)
            return {"sentences": [], "values": values[:4]} if values else {}
        sentences = cls._sentences_matching(cls._clean_evidence_text(evidence), ["slack", "not used", "unused", "remaining", "binding"])
        values = []
        for sentence in sentences:
            preferred = re.findall(r"\bor\s+(\d+(?:\.\d+)?\s*(?:ft\^?2|ft\$?\^?2|lb|hours?|units?|%)?)", sentence, flags=re.IGNORECASE)
            for match in preferred:
                clean = re.sub(r"\s+", " ", match.replace("$", "")).strip()
                if clean and clean not in values:
                    values.append(clean)
            if values:
                continue
            unit_values = re.findall(r"\b\d+(?:\.\d+)?\s*(?:ft\^?2|ft\$?\^?2|lb|hours?|units?|%)", sentence, flags=re.IGNORECASE)
            for match in unit_values:
                clean = re.sub(r"\s+", " ", match.replace("$", "")).strip()
                if clean and clean not in values:
                    values.append(clean)
            if values:
                continue
            for match in re.findall(r"\b\d+(?:\.\d+)?\s*(?:ft\^?2|ft\$?\^?2|lb|hours?|units?|%)?|\$?\b\d+(?:\.\d+)?\b", sentence, flags=re.IGNORECASE):
                clean = re.sub(r"\s+", " ", match.replace("$", "")).strip()
                if clean and clean not in values:
                    values.append(clean)
        values = cls._clean_slack_values(values)
        return {"sentences": sentences[:2], "values": values[:4]} if sentences else {}

    @classmethod
    def _extract_software_actions(cls, evidence: str) -> List[str]:
        actions = []
        chunks = []
        for line in cls._clean_evidence_text(evidence).splitlines():
            chunks.extend(re.split(r"(?<=[.!?])\s+", line))
        for line in chunks:
            clean = line.strip().lstrip("-*•").strip()
            lower = clean.lower()
            if any(word in lower for word in ["click", "input", "solve", "save", "print", "open", "entry", "cancel"]):
                clean = re.sub(r"\s+", " ", clean)
                if len(clean) > 140:
                    for part in re.split(r"\b(?:to|and)\b", clean, flags=re.IGNORECASE):
                        part = part.strip(" .;:")
                        if 5 <= len(part) <= 140 and any(word in part.lower() for word in ["click", "input", "solve", "save", "print", "open", "entry", "cancel"]):
                            actions.append(part)
                elif 5 <= len(clean):
                    actions.append(clean)
        return actions[:6]

    @staticmethod
    def _action_tokens(action: str) -> List[str]:
        return [token for token in re.findall(r"[a-z]+", action.lower()) if len(token) >= 4]

    @staticmethod
    def _extract_formulas(text: str) -> List[str]:
        text = ContentQualityAgent._clean_evidence_text(text)
        formulas = re.findall(r"\$\$(.*?)\$\$", text, flags=re.DOTALL)
        formulas.extend(re.findall(r"\$([^$]+)\$", text))
        return [re.sub(r"\s+", " ", formula).strip() for formula in formulas if formula.strip()]

    @staticmethod
    def _clean_evidence_text(text: str) -> str:
        text = re.sub(r"--- Page\s+\d+\s+evidence ---", " ", text)
        text = re.sub(r"#\s*Dagon University Research Journal\s+\d{4},\s*Vol\.\s*\d+\s*\d*", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
        text = re.sub(r"\*Figure:[^*]+\*", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"#{1,6}\s*", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _contains_formula(cls, content_l: str, formula: str) -> bool:
        tokens = re.findall(r"[a-z]\d*|\d+(?:\.\d+)?", cls._normalise_for_match(formula))
        important = [token for token in tokens if len(token) > 1 or token.isdigit()]
        if not important:
            return False
        hits = sum(1 for token in important if token in content_l)
        return hits >= max(2, min(len(important), 4))

    @classmethod
    def _contains_enough_constraints(cls, content_l: str, constraints: List[str]) -> bool:
        if "<=" not in content_l and ">=" not in content_l and "less than or equal" not in content_l and "greater than or equal" not in content_l:
            return False
        required = min(2, len(constraints))
        hits = sum(1 for constraint in constraints if cls._contains_formula(content_l, constraint))
        return hits >= required

    @staticmethod
    def _contains_values(content_l: str, values: List[str]) -> bool:
        checks = []
        for value in values:
            variable_match = re.search(r"([A-Za-z]\d*)\s*=\s*(-?\d+(?:\.\d+)?)", value)
            if variable_match:
                checks.append((variable_match.group(1).lower(), variable_match.group(2)))
            else:
                numeric = re.sub(r"[^0-9.\-]", "", value)
                if numeric:
                    number_match = re.search(r"-?\d+(?:\.\d+)?", value)
                    unit_match = re.search(r"(ft\^?2|lb|hours?|units?|%)", value, flags=re.IGNORECASE)
                    checks.append(("", numeric, number_match.group(0) if number_match else numeric, unit_match.group(1).lower() if unit_match else ""))
        if not checks:
            return False
        hits = 0
        for check in checks:
            variable = check[0]
            value = check[1]
            if variable:
                pattern = rf"{re.escape(variable)}\s*=\s*{re.escape(value)}"
                if re.search(pattern, content_l):
                    hits += 1
            else:
                display_number = check[2] if len(check) > 2 else value
                unit = check[3] if len(check) > 3 else ""
                if value in content_l or display_number in content_l:
                    if not unit or unit.replace("^", "") in content_l.replace("^", ""):
                        hits += 1
        return hits >= min(2, len(checks))

    @classmethod
    def _fact_supported_in_content(cls, content_l: str, fact: str) -> bool:
        fact_l = cls._normalise_for_match(fact)
        if "=" in fact_l and any(op in fact_l for op in ["<=", ">="]):
            return cls._contains_formula(content_l, fact)
        variable_match = re.search(r"([a-z]\d*)\s*=\s*(-?\d+(?:\.\d+)?)", fact_l)
        if variable_match:
            return bool(re.search(rf"{re.escape(variable_match.group(1))}\s*=\s*{re.escape(variable_match.group(2))}", content_l))
        numeric = re.findall(r"\d+(?:\.\d+)?", fact_l)
        keywords = [token for token in re.findall(r"[a-z]+", fact_l) if len(token) >= 4]
        numeric_hit = any(value in content_l for value in numeric) if numeric else False
        keyword_hit = any(token in content_l for token in keywords) if keywords else False
        return numeric_hit or keyword_hit

    @classmethod
    def _sentence_overlap(cls, content_l: str, sentence: str) -> bool:
        tokens = [token for token in re.findall(r"[a-z]+|\d+(?:\.\d+)?", cls._normalise_for_match(sentence)) if len(token) >= 4 or token.isdigit()]
        if not tokens:
            return False
        hits = sum(1 for token in tokens if token in content_l)
        return hits >= min(2, len(tokens))

    @staticmethod
    def _sentences_matching(text: str, keywords: List[str]) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        result = []
        for sentence in sentences:
            clean = re.sub(r"\s+", " ", sentence).strip()
            lower = clean.lower()
            if clean and any(keyword in lower for keyword in keywords):
                result.append(clean)
        return result[:6]

    @staticmethod
    def _missing_title_anchors(title: str, lower_text: str) -> List[str]:
        title_l = title.lower()
        groups = []
        if "slack" in title_l:
            groups.append(("slack interpretation", ["slack", "unused", "remaining", "not used", "binding"]))
        if "objective" in title_l:
            groups.append(("objective function", ["objective", "maximize", "minimize", "profit", "income", "="]))
        elif "constraint" in title_l:
            groups.append(("constraints", ["constraint", "<=", ">=", "subject to", "available"]))
        elif "optimal" in title_l or "production result" in title_l:
            groups.append(("optimal result", ["optimal", "maximum", "minimum", "profit", "income", "="]))
        elif "graphical" in title_l or "feasible" in title_l:
            groups.append(("graphical method", ["graph", "feasible", "region", "constraint"]))
        elif "model" in title_l or "formulat" in title_l:
            groups.append(("model formulation", ["model", "variable", "objective", "constraint", "x1", "x2"]))
        missing = []
        for label, anchors in groups:
            if not any(anchor in lower_text for anchor in anchors):
                missing.append(label)
        return missing

    @classmethod
    def _normalise_content(cls, content: Any, fallback: Any) -> Any:
        if isinstance(content, list):
            items = []
            for item in content:
                if not isinstance(item, str):
                    continue
                for line in item.splitlines():
                    line = cls._clean_bullet(line)
                    if line and not cls._is_bad_line(line):
                        items.append(line)
            if len(items) >= 3:
                return items[:5]
        fallback_items = cls._fallback_items(fallback)
        return fallback_items[:5]

    @classmethod
    def _fallback_content(cls, slide: SlideContent, evidence: str, packet: Dict[str, Any] | None = None) -> List[str]:
        deterministic = cls._deterministic_content(slide, evidence, packet)
        if deterministic:
            return deterministic
        candidates = cls._fallback_items(evidence)
        title_terms = [t for t in re.findall(r"[A-Za-z0-9]+", slide.slide.slide_title.lower()) if len(t) > 3]
        ranked = []
        for item in candidates:
            if cls._is_bad_line(item):
                continue
            score = sum(1 for term in title_terms if term in item.lower())
            ranked.append((score, item))
        ranked.sort(key=lambda pair: (-pair[0], len(pair[1])))
        bullets = [item for _, item in ranked[:5]]
        while len(bullets) < 3:
            bullets.append(slide.slide.goal[:90])
        return bullets[:5]

    @classmethod
    def _apply_deterministic_fallbacks(
        cls,
        slides: List[SlideContent],
        unresolved: Dict[int, List[str]],
        evidence_by_number: Dict[int, str],
        packet_by_number: Dict[int, Dict[str, Any]] | None = None,
    ) -> List[SlideContent]:
        repaired = []
        unresolved_numbers = set(unresolved)
        packet_by_number = packet_by_number or {}
        for slide in slides:
            if slide.slide.slide_number in unresolved_numbers:
                content = cls._deterministic_content(
                    slide,
                    evidence_by_number.get(slide.slide.slide_number, ""),
                    packet_by_number.get(slide.slide.slide_number),
                )
                if content:
                    repaired.append(SlideContent(slide=slide.slide, content=content))
                    continue
            repaired.append(slide)
        return repaired

    @classmethod
    def _deterministic_content(cls, slide: SlideContent, evidence: str, packet: Dict[str, Any] | None = None) -> List[str]:
        title_l = slide.slide.slide_title.lower()
        evidence_l = cls._normalise_for_match(evidence)
        packet_checks = (packet or {}).get("required_checks", [])
        packet_content = cls._deterministic_from_packet_checks(packet_checks, evidence)
        if packet_content:
            return packet_content
        objective = cls._extract_objective_formula(evidence)
        objective_check = next((check for check in packet_checks if check.get("kind") == "objective_formula"), None)
        if objective_check and objective_check.get("formula"):
            objective = str(objective_check.get("formula"))
        if objective:
            bullets = [f"Objective function: ${objective}$"]
            direction = cls._objective_direction(evidence)
            if direction:
                bullets.insert(0, direction)
            bullets.extend(cls._variable_bullets(evidence))
            return cls._pad_bullets(bullets, "Decision variables define the model choice")
        slack = cls._extract_slack_facts(evidence)
        slack_check = next((check for check in packet_checks if check.get("kind") == "slack_facts"), None)
        if slack_check:
            slack = {
                "values": cls._clean_slack_values([str(item) for item in slack_check.get("values", []) if str(item).strip()]),
                "sentences": [str(item) for item in slack_check.get("sentences", []) if str(item).strip()],
            }
        if slack:
            bullets = []
            for sentence in slack.get("sentences", [])[:2]:
                bullets.append(cls._trim_bullet(sentence))
            if slack.get("values"):
                bullets.append("Slack value(s): " + ", ".join(slack["values"][:3]))
            bullets.append("Slack identifies non-binding resources")
            return cls._pad_bullets(bullets, "Binding constraints are fully used")
        constraints = cls._extract_constraints(evidence)
        constraint_check = next((check for check in packet_checks if check.get("kind") == "constraints"), None)
        if constraint_check:
            constraints = [str(item) for item in constraint_check.get("items", []) if str(item).strip()]
        if constraints:
            bullets = [f"Constraint: ${constraint}$" for constraint in constraints[:4]]
            bullets.append("Subject to resource limits")
            return cls._pad_bullets(bullets, "Non-negativity conditions apply")
        values = cls._extract_result_values(evidence)
        value_check = next((check for check in packet_checks if check.get("kind") == "result_values"), None)
        if value_check:
            values = [str(item) for item in value_check.get("items", []) if str(item).strip()]
        if values:
            bullets = []
            variable_values = [value for value in values if "=" in value]
            scalar_values = [value for value in values if "=" not in value]
            if variable_values:
                bullets.append("Optimal decision values: " + ", ".join(variable_values[:3]))
            if scalar_values:
                bullets.append("Objective value(s): " + ", ".join(scalar_values[:3]))
            for sentence in cls._sentences_matching(cls._clean_evidence_text(evidence), ["optimal", "maximum", "minimum", "profit", "income"])[:2]:
                bullets.append(cls._trim_bullet(sentence))
            return cls._pad_bullets(bullets, "Translate numerical result to the scenario")
        if ("graph" in title_l or "feasible" in title_l) and "feasible region" in evidence_l:
            return [
                "Plot constraints on the $x_1$-$x_2$ plane",
                "Inequalities define bounded half-plane regions",
                "Common shaded area: feasible solution space",
                "Optimal solution must lie in feasible region",
            ]
        actions = cls._extract_software_actions(evidence)
        action_check = next((check for check in packet_checks if check.get("kind") == "workflow_actions"), None)
        required_actions = [str(item) for item in action_check.get("items", []) if str(item).strip()] if action_check else cls._extract_required_workflow_actions(evidence)
        if required_actions:
            actions = required_actions + [action for action in actions if action not in required_actions]
        if actions:
            bullets = [cls._trim_bullet(action) for action in actions[:5]]
            return cls._pad_bullets(bullets, "Software executes the modeled optimization")
        if packet and packet.get("required_facts"):
            return cls._pad_bullets([str(item) for item in packet.get("required_facts", [])[:5]], slide.slide.goal[:90])
        return []

    @classmethod
    def _deterministic_from_packet_checks(cls, packet_checks: List[Dict[str, Any]], evidence: str) -> List[str]:
        if not packet_checks:
            return []
        check = packet_checks[0]
        kind = str(check.get("kind") or "").strip().lower()
        if kind == "objective_formula" and check.get("formula"):
            objective = str(check.get("formula"))
            bullets = [f"Objective function: ${objective}$"]
            direction = cls._objective_direction(evidence)
            if direction:
                bullets.insert(0, direction)
            return cls._pad_bullets(bullets, "Decision variables define the model choice")
        if kind == "constraints":
            constraints = [str(item) for item in check.get("items", []) if str(item).strip()]
            if constraints:
                bullets = [f"Constraint: ${constraint}$" for constraint in constraints[:4]]
                bullets.append("Subject to resource limits")
                return cls._pad_bullets(bullets, "Non-negativity conditions apply")
        if kind == "result_values":
            values = [str(item) for item in check.get("items", []) if str(item).strip()]
            if values:
                variable_values = [value for value in values if "=" in value]
                scalar_values = [value for value in values if "=" not in value]
                bullets = []
                if variable_values:
                    bullets.append("Optimal decision values: " + ", ".join(variable_values[:3]))
                if scalar_values:
                    bullets.append("Objective value(s): " + ", ".join(scalar_values[:3]))
                bullets.append("Translate numerical result to the scenario")
                return cls._pad_bullets(bullets, "Result values come from the source solution")
        if kind == "slack_facts":
            values = cls._clean_slack_values([str(item) for item in check.get("values", []) if str(item).strip()])
            sentences = [str(item) for item in check.get("sentences", []) if str(item).strip()]
            if values or sentences:
                bullets = [cls._trim_bullet(sentence) for sentence in sentences[:2]]
                if values:
                    bullets.append("Slack value: " + ", ".join(values[:2]))
                bullets.append("Slack identifies a non-binding resource")
                return cls._pad_bullets(bullets, "Binding constraints are fully used")
        if kind == "workflow_actions":
            actions = [str(item) for item in check.get("items", []) if str(item).strip()]
            if actions:
                return cls._pad_bullets([cls._trim_bullet(action) for action in actions[:5]], "Software executes the modeled optimization")
        return []

    @staticmethod
    def _extract_required_workflow_actions(evidence: str) -> List[str]:
        actions = []
        normalized = re.sub(r"\s+", " ", evidence)
        for match in re.findall(r"Workflow action:\s*(.*?)(?=Workflow action:|$)", normalized, flags=re.IGNORECASE):
            action = match.strip(" .;:-")
            if action:
                actions.append(action)
        if actions:
            return actions[:6]
        for line in evidence.splitlines():
            clean = line.strip()
            if clean.lower().startswith("workflow action:"):
                action = clean.split(":", 1)[1].strip()
                if action:
                    actions.append(action)
        return actions[:6]

    @staticmethod
    def _objective_direction(evidence: str) -> str:
        lower = evidence.lower()
        if "maximize" in lower or "maximise" in lower:
            return "Direction: maximize objective value"
        if "minimize" in lower or "minimise" in lower:
            return "Direction: minimize objective value"
        return ""

    @staticmethod
    def _variable_bullets(evidence: str) -> List[str]:
        bullets = []
        for match in re.findall(r"([A-Za-z]\s*_?\s*\d+)\s*[,=:]\s*([^.\n;]{3,80})", evidence):
            var = re.sub(r"\s+", "", match[0])
            desc = re.sub(r"\s+", " ", match[1]).strip()
            if desc:
                bullets.append(f"${var}$: {desc}")
        return bullets[:2]

    @staticmethod
    def _pad_bullets(bullets: List[str], fallback: str) -> List[str]:
        clean = []
        for bullet in bullets:
            bullet = ContentQualityAgent._trim_bullet(bullet)
            if bullet and bullet not in clean and not ContentQualityAgent._is_bad_line(bullet):
                clean.append(bullet)
        while len(clean) < 3:
            clean.append(fallback)
        return clean[:5]

    @staticmethod
    def _trim_bullet(text: str) -> str:
        text = ContentQualityAgent._clean_bullet(text)
        text = re.sub(r"\s+", " ", text).strip(" .;:-")
        return text[:140]

    @staticmethod
    def _fallback_items(value: Any) -> List[str]:
        text = ContentQualityAgent._flatten(value)
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        items = []
        for part in parts:
            item = part.strip().lstrip("-*•").strip()
            item = ContentQualityAgent._clean_bullet(item)
            if 8 <= len(item) <= 140 and not ContentQualityAgent._is_bad_line(item):
                items.append(item)
        return items or [text[:120]] if text.strip() else []

    @classmethod
    def _is_bad_line(cls, line: str) -> bool:
        lower = line.strip().lower()
        if not lower:
            return True
        if re.fullmatch(r"\d{1,3}\.?", lower):
            return True
        if re.fullmatch(r"(berlin,\s*)?den\s+\d{1,2}\.?", lower):
            return True
        if re.fullmatch(r"[a-zäöüß]+,\s*den\s+\d{1,2}\.?", lower):
            return True
        if "![ " in lower or lower.startswith("![") or re.search(r"\.(jpeg|jpg|png|webp)\)", lower):
            return True
        if re.search(r"\*figure:|figure:", lower):
            return True
        if lower.startswith("#"):
            return True
        if cls._has_noisy_slack_values(line):
            return True
        return any(re.search(pattern, lower) for pattern in cls.BAD_PATTERNS)

    @staticmethod
    def _clean_bullet(line: str) -> str:
        line = line.strip().lstrip("-*•").strip()
        line = re.sub(r"\$(\d+(?:\.\d+)?)(?=([.,;:]|$))", r"$\1$", line)
        return re.sub(r"\s+", " ", line).strip()

    @staticmethod
    def _has_unbalanced_math(text: str) -> bool:
        return text.count("$") % 2 == 1

    @staticmethod
    def _has_noisy_slack_values(text: str) -> bool:
        for line in text.splitlines():
            lower = line.lower()
            if re.search(r"slack value(?:s)?\s+(?:include|are|is|:)", lower):
                numbers = re.findall(r"\d+(?:\.\d+)?", line)
                if len(numbers) > 1:
                    return True
        return False

    @staticmethod
    def _clean_slack_values(values: List[str]) -> List[str]:
        clean_values = []
        unit_values = []
        for value in values:
            clean = re.sub(r"\s+", " ", str(value).replace("$", "")).strip(" ,.;:")
            if not clean:
                continue
            if re.search(r"(ft\^?2|lb|hours?|units?|%)", clean, flags=re.IGNORECASE):
                unit_values.append(clean)
            clean_values.append(clean)
        selected = unit_values or clean_values[:1]
        result = []
        for value in selected:
            if value not in result:
                result.append(value)
        return result[:2]

    @staticmethod
    def _flatten(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return " ".join(ContentQualityAgent._flatten(item) for item in value)
        if isinstance(value, dict):
            chunks = []
            for key, val in value.items():
                chunks.append(str(key))
                chunks.append(ContentQualityAgent._flatten(val))
            return " ".join(chunks)
        return str(value or "")

    @staticmethod
    def _bullet_count(content: Any) -> int:
        if isinstance(content, list):
            return len([item for item in content if isinstance(item, str) and item.strip()])
        if isinstance(content, dict):
            return sum(ContentQualityAgent._bullet_count(v) for v in content.values())
        if isinstance(content, str):
            if "|" in content and "\n" in content:
                return 3
            return len([line for line in content.splitlines() if line.strip()])
        return 0

    @staticmethod
    def _chunks(items: List[SlideContent], size: int) -> List[List[SlideContent]]:
        return [items[i : i + size] for i in range(0, len(items), size)]
