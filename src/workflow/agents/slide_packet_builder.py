from dataclasses import asdict
import re
from typing import Any, Dict, List

from src.models.context import DocumentContext
from src.models.slide import Slide
from src.ingestion.compact_context import ensure_compact_context
from src.workflow.agents.content_quality import ContentQualityAgent


class SlidePacketBuilderAgent:
    MAX_EVIDENCE_CHARS = 3600

    def __init__(self, model: str):
        self.content_tools = ContentQualityAgent(model)

    def build_packets(self, slide_specs: List[Slide], context: DocumentContext) -> List[Dict[str, Any]]:
        packets = []
        used_fact_keys: set[str] = set()
        global_numbered_facts = self._all_global_numbered_facts(context)
        list_specs_count = len(slide_specs) if len(global_numbered_facts) >= 6 else sum(1 for spec in slide_specs if self._likely_list_slide(spec))
        used_numbered_keys: set[str] = set()
        list_index = 0
        for spec in slide_specs:
            evidence = self._safe_evidence(self.content_tools._retrieve_evidence(context, self._empty_slide(spec)))
            intent = self._infer_intent(spec)
            role = self._infer_role(spec)
            coverage_mode = self._coverage_mode(spec, evidence, intent)
            if coverage_mode != "list_coverage" and global_numbered_facts and self._document_supports_numbered_coverage(context, spec):
                coverage_mode = "list_coverage"
            facts = self._required_facts(spec, evidence, intent)
            role_facts = self._role_anchor_facts(evidence, role)
            source_candidates = [] if coverage_mode == "list_coverage" else self._source_fact_candidates(evidence, role)
            coverage_items = self._coverage_items(spec, evidence, intent)
            if coverage_mode == "list_coverage" and global_numbered_facts:
                coverage_items = self._numbered_items_for_slide(spec, global_numbered_facts, used_numbered_keys, list_index, max(1, list_specs_count))
                list_index += 1
            elif len(coverage_items) < 3 and coverage_mode == "list_coverage":
                coverage_items = self._dedupe_coverage(coverage_items + self._global_numbered_facts(context, spec))[:6]
            if coverage_mode == "list_coverage":
                facts = self._dedupe_coverage(coverage_items + facts)[:10]
            else:
                ranked_facts = self._prioritize_facts(spec, role, self._dedupe(role_facts + facts + source_candidates), used_fact_keys)
                facts = self._merge_forced_role_facts(role, role_facts, ranked_facts)[:10]
            for fact in facts[:5]:
                used_fact_keys.add(self._fact_key(fact))
            checks = self._required_checks(spec, evidence, facts, intent)
            role_check = self._role_anchor_check(role, facts)
            if role_check:
                checks.append(role_check)
            if coverage_items and coverage_mode == "list_coverage":
                checks.append({"kind": "coverage_items", "items": coverage_items[:6], "min_hits": min(3, len(coverage_items))})
            packet = {
                "slide_number": spec.slide_number,
                "slide_title": spec.slide_title,
                "slide_type": spec.slide_type.value if hasattr(spec.slide_type, "value") else str(spec.slide_type),
                "goal": spec.goal,
                "intent": intent,
                "role": role,
                "coverage_mode": coverage_mode,
                "source_pages": self._source_pages(evidence),
                "required_facts": facts,
                "required_checks": checks,
                "coverage_items": coverage_items[:6],
                "evidence": self.content_tools._sentence_safe_truncate(evidence, self.MAX_EVIDENCE_CHARS),
            }
            if spec.table:
                packet["table"] = asdict(spec.table)
            if spec.latex_block_formula:
                packet["latex_block_formula"] = spec.latex_block_formula
            packets.append(packet)
        return packets

    def _required_facts(self, spec: Slide, evidence: str, intent: str) -> List[str]:
        facts: List[str] = []
        numbered_facts = self._numbered_evidence_facts(evidence, spec.slide_title, spec.goal)
        objective = self.content_tools._extract_objective_formula(evidence)
        constraints = self.content_tools._extract_constraints(evidence)
        values = self.content_tools._extract_result_values(evidence)
        slack = self.content_tools._extract_slack_facts(evidence)
        actions = self.content_tools._extract_required_workflow_actions(evidence) or self.content_tools._extract_software_actions(evidence)
        if spec.table:
            facts.append(f"Use table: {spec.table.table_caption}")
        if objective and self._intent_requires(intent, "objective_formula"):
            facts.append(f"Objective formula: {objective}")
        if constraints and self._intent_requires(intent, "constraints"):
            facts.extend([f"Constraint: {item}" for item in constraints[:4]])
        if values and self._intent_requires(intent, "result_values"):
            facts.append("Result values: " + ", ".join(values[:6]))
        if slack and self._intent_requires(intent, "slack_facts"):
            if slack.get("sentences"):
                facts.extend(slack["sentences"][:2])
            if slack.get("values"):
                facts.append("Slack values: " + ", ".join(slack["values"][:4]))
        if actions and self._intent_requires(intent, "workflow_actions"):
            facts.extend([f"Workflow action: {item}" for item in actions[:5]])
        if numbered_facts and intent in {"generic", "concept_intro"}:
            facts.extend(numbered_facts)
        if not facts:
            facts.extend(self._generic_evidence_facts(evidence, spec.slide_title))
        return self._dedupe(facts)[:8]

    def _coverage_items(self, spec: Slide, evidence: str, intent: str) -> List[str]:
        mode = self._coverage_mode(spec, evidence, intent)
        if mode == "list_coverage":
            return self._numbered_evidence_facts(evidence, spec.slide_title, spec.goal)[:6]
        if mode == "reference_synthesis":
            return self._reference_evidence_facts(evidence, spec.slide_title)[:6]
        return []

    def _coverage_mode(self, spec: Slide, evidence: str, intent: str) -> str:
        title_goal = f"{spec.slide_title} {spec.goal}".lower()
        numbered = self._extract_numbered_items(evidence)
        if numbered and (len(numbered) >= 4 or any(term in title_goal for term in ["principle", "principles", "guideline", "steps", "key", "core", "recommendation"])):
            return "list_coverage"
        if self._looks_reference_heavy(evidence) and intent in {"generic", "concept_intro"}:
            return "reference_synthesis"
        return "normal"

    def _global_numbered_facts(self, context: DocumentContext, spec: Slide) -> List[str]:
        compact = ensure_compact_context(context)
        items = []
        for card in compact.get("page_cards", []):
            for item in card.get("numbered_items", []):
                if item.get("number") is not None and item.get("text"):
                    if SlidePacketBuilderAgent._looks_like_reference_item(str(item.get("text", ""))):
                        continue
                    items.append({"number": int(item["number"]), "text": str(item["text"])})
        if not items:
            return []
        query_terms = self._query_terms_for_list(f"{spec.slide_title} {spec.goal}")
        ranked = []
        for item in items:
            lower = item["text"].lower()
            score = sum(2 for term in query_terms if term in lower)
            ranked.append((score, item["number"], item["text"]))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        if ranked and ranked[0][0] > 0:
            selected = ranked[:6]
        else:
            selected = ranked[:6]
        return [f"Principle {number}: {text}" for _, number, text in selected]

    @staticmethod
    def _all_global_numbered_facts(context: DocumentContext) -> List[str]:
        compact = ensure_compact_context(context)
        by_number: Dict[int, str] = {}
        for card in compact.get("page_cards", []):
            for item in card.get("numbered_items", []):
                if item.get("number") is None or not item.get("text"):
                    continue
                number = int(item["number"])
                text = re.sub(r"\s+", " ", str(item["text"])).strip(" -;:")
                text = re.sub(r"\s+---.*$", "", text).strip()
                if SlidePacketBuilderAgent._looks_like_reference_item(text):
                    continue
                if len(text) < 12:
                    continue
                if number not in by_number or len(text) > len(by_number[number]):
                    by_number[number] = text
        return [f"Principle {number}: {by_number[number]}" for number in sorted(by_number)]

    @staticmethod
    def _likely_list_slide(spec: Slide) -> bool:
        scope = f"{spec.slide_title} {spec.goal}".lower()
        return any(term in scope for term in ["principle", "principles", "guideline", "guidelines", "steps", "recommendation", "recommendations", "checklist"])

    @staticmethod
    def _document_supports_numbered_coverage(context: DocumentContext, spec: Slide) -> bool:
        scope = f"{context.document_id} {context.source_file} {spec.slide_title} {spec.goal}".lower()
        return any(term in scope for term in ["principle", "principles", "guideline", "guidelines", "ten principles", "steps", "checklist"])

    @staticmethod
    def _looks_like_reference_item(text: str) -> bool:
        lower = text.lower()
        if re.search(r"https?://|doi\.org|www\.|retrieved from|accessed on", lower):
            return True
        if re.search(r"\b(?:19|20)\d{2}\b", text) and re.search(r"\b(journal|vol\.|issue|press|conference|doi|isbn|http|retrieved|publication)\b", lower):
            return True
        if re.match(r"^[A-ZÀ-Ỹ][A-Za-zÀ-ỹ'’-]+,\s+[A-Z]", text):
            return True
        return False

    @staticmethod
    def _numbered_items_for_slide(spec: Slide, items: List[str], used_keys: set[str], index: int, total: int) -> List[str]:
        if not items:
            return []
        target = max(2, min(4, (len(items) + total - 1) // total if total else 4))
        title_terms = [
            term
            for term in re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", f"{spec.slide_title} {spec.goal}".lower())
            if term not in {"principle", "principles", "citizen", "science", "public", "project", "projects", "section", "content", "conclusion", "introduction", "overview"}
        ]
        scope = f"{spec.slide_title} {spec.goal}".lower()
        preferred_numbers = set()
        if any(term in scope for term in ["evaluation", "evaluating", "assessment"]):
            preferred_numbers.add(9)
        if any(term in scope for term in ["leadership", "leader", "ethical", "legal", "rights", "copyright", "privacy"]):
            preferred_numbers.add(10)
        if any(term in scope for term in ["data", "metadata", "sharing", "open"]):
            preferred_numbers.add(7)
        if any(term in scope for term in ["recognition", "publication", "acknowledg"]):
            preferred_numbers.add(8)
        ranked = []
        for pos, item in enumerate(items):
            key = SlidePacketBuilderAgent._fact_key(item)
            lower = item.lower()
            score = sum(3 for term in title_terms if term in lower)
            number_match = re.match(r"\s*Principle\s+(\d+):", item, flags=re.IGNORECASE)
            if number_match and int(number_match.group(1)) in preferred_numbers:
                score += 12
            if key in used_keys:
                score -= 6
            ranked.append((score, pos, key, item))
        preferred = [row for row in sorted(ranked, key=lambda row: (-row[0], row[1])) if row[0] > 0]
        start = min(len(items), index * target)
        unused_sequential = []
        used_sequential = []
        for offset in range(len(items)):
            pos = (start + offset) % len(items)
            item = items[pos]
            key = SlidePacketBuilderAgent._fact_key(item)
            row = (0 if key not in used_keys else -6, pos, key, item)
            if key in used_keys:
                used_sequential.append(row)
            else:
                unused_sequential.append(row)
        selected = []
        for _, _, key, item in preferred + unused_sequential + used_sequential:
            if key in {SlidePacketBuilderAgent._fact_key(existing) for existing in selected}:
                continue
            if key in used_keys and len(selected) >= max(1, target - 1):
                continue
            selected.append(item)
            used_keys.add(key)
            if len(selected) >= target:
                break
        return selected

    def _required_checks(self, spec: Slide, evidence: str, facts: List[str], intent: str) -> List[Dict[str, Any]]:
        checks: List[Dict[str, Any]] = []
        objective = self.content_tools._extract_objective_formula(evidence)
        constraints = self.content_tools._extract_constraints(evidence)
        values = self.content_tools._extract_result_values(evidence)
        slack = self.content_tools._extract_slack_facts(evidence)
        actions = self.content_tools._extract_required_workflow_actions("\n".join(facts)) or self.content_tools._extract_software_actions(evidence)
        if objective and self._intent_requires(intent, "objective_formula"):
            checks.append({"kind": "objective_formula", "formula": objective})
        if constraints and self._intent_requires(intent, "constraints"):
            checks.append({"kind": "constraints", "items": constraints[:4]})
        if values and self._intent_requires(intent, "result_values"):
            checks.append({"kind": "result_values", "items": values[:6]})
        if slack and self._intent_requires(intent, "slack_facts"):
            checks.append(
                {
                    "kind": "slack_facts",
                    "values": slack.get("values", [])[:4],
                    "sentences": slack.get("sentences", [])[:2],
                }
            )
        if actions and self._intent_requires(intent, "workflow_actions"):
            checks.append({"kind": "workflow_actions", "items": actions[:5]})
        return checks

    @staticmethod
    def _infer_intent(spec: Slide) -> str:
        title = spec.slide_title.lower()
        goal = spec.goal.lower()
        scope = f"{title} {goal}"
        if re.search(r"\b(software|workflow|input|inputting|entry|saving|save|tool|procedure|step-by-step|click|solve)\b", scope):
            return "procedure"
        if "slack" in scope or "binding" in scope or "unused" in scope:
            return "slack_interpretation"
        if any(word in title for word in ["graph", "feasible", "plot"]):
            return "visual_method"
        if any(word in title for word in ["optimal", "result", "profit", "income", "solution value"]):
            return "result_interpretation"
        if "objective" in title:
            return "objective_formula"
        if "constraint" in title:
            return "constraints"
        if any(word in title for word in ["model", "formulat", "product mix"]):
            return "model_formulation"
        if any(word in title for word in ["definition", "introduction", "background", "application", "scope"]):
            return "concept_intro"
        return "generic"

    @staticmethod
    def _infer_role(spec: Slide) -> str:
        title = spec.slide_title.lower()
        goal = spec.goal.lower()
        scope = f"{title} {goal}"
        if re.match(r"^\d+\.\s+", title) and not re.match(r"^\d+\.\d+", title):
            return "overview"
        if "knowledge transfer" in scope and "assessment" in scope:
            return "overview"
        if any(term in scope for term in ["overview", "introduction", "main theme", "scope", "background"]):
            return "overview"
        if any(term in scope for term in ["dissemination", "outreach", "public talks", "publication", "education", "audience"]):
            return "dissemination"
        if any(term in scope for term in ["readiness", "trl", "progression", "prototype"]):
            return "progression"
        if any(term in scope for term in ["commercial", "industry", "collaboration", "launch", "product development", "transfer"]):
            return "commercialization"
        if any(term in scope for term in ["technology", "method", "mechanism", "manufacturing", "coloured", "colored"]):
            return "mechanism"
        if any(term in scope for term in ["result", "impact", "implication", "conclusion"]):
            return "implication"
        return "supporting_detail"

    @staticmethod
    def _intent_requires(intent: str, fact_type: str) -> bool:
        required_by_intent = {
            "model_formulation": {"objective_formula", "constraints"},
            "objective_formula": {"objective_formula"},
            "constraints": {"constraints"},
            "result_interpretation": {"result_values"},
            "slack_interpretation": {"slack_facts"},
            "procedure": {"workflow_actions"},
        }
        return fact_type in required_by_intent.get(intent, set())

    @staticmethod
    def _generic_evidence_facts(evidence: str, title: str = "") -> List[str]:
        facts = []
        title_terms = [
            term
            for term in re.findall(r"[a-z0-9_]{4,}", title.lower())
            if term not in {"introduction", "method", "solution", "section", "content"}
        ]
        text = ContentQualityAgent._clean_evidence_text(evidence)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        ranked = []
        for sentence in sentences:
            clean = sentence.strip()
            lower = clean.lower()
            if not clean or clean.startswith("---") or "dagon university research journal" in lower:
                continue
            if SlidePacketBuilderAgent._looks_like_heading_noise(clean):
                continue
            if SlidePacketBuilderAgent._looks_truncated(clean):
                continue
            score = sum(1 for term in title_terms if term in lower)
            if score == 0 and re.search(r"objective formula|result values|slack values|constraint:", lower):
                continue
            if score > 0 or re.search(r"\d|objective|constraint|software|application|model|optimal|feasible", lower):
                ranked.append((score, ContentQualityAgent._sentence_safe_truncate(clean, 180)))
        ranked.sort(key=lambda item: (-item[0], len(item[1])))
        for _, fact in ranked:
            if fact not in facts:
                facts.append(fact)
            if len(facts) >= 4:
                break
        return facts

    @staticmethod
    def _source_fact_candidates(evidence: str, role: str) -> List[str]:
        text = ContentQualityAgent._clean_evidence_text(evidence)
        raw_parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        candidates: List[str] = []
        for part in raw_parts:
            clean = re.sub(r"\s+", " ", part).strip(" ;:-")
            if not clean or len(clean) < 35:
                continue
            if SlidePacketBuilderAgent._looks_truncated(clean) or SlidePacketBuilderAgent._looks_like_heading_noise(clean):
                continue
            if SlidePacketBuilderAgent._candidate_matches_role(clean, role):
                candidates.append(clean)
            if len(clean) > 180:
                for clause in re.split(r",\s+|;\s+|\s+\b(?:while|through|which|leading to|resulting in)\b\s+", clean):
                    clause = re.sub(r"\s+", " ", clause).strip(" ;:-")
                    if 45 <= len(clause) <= 220 and not SlidePacketBuilderAgent._looks_like_heading_noise(clause) and not SlidePacketBuilderAgent._looks_like_fragment(clause) and SlidePacketBuilderAgent._candidate_matches_role(clause, role):
                        candidates.append(clause)
        return SlidePacketBuilderAgent._dedupe_by_overlap(
            [ContentQualityAgent._sentence_safe_truncate(item, 240) for item in candidates]
        )[:18]

    @staticmethod
    def _role_anchor_facts(evidence: str, role: str) -> List[str]:
        text = ContentQualityAgent._clean_evidence_text(evidence)
        sentences = [re.sub(r"\s+", " ", item).strip(" ;:-") for item in re.split(r"(?<=[.!?])\s+|\n+", text)]
        anchors = SlidePacketBuilderAgent._role_anchor_terms(role)
        facts = []
        for sentence in sentences:
            lower = sentence.lower()
            if not sentence or SlidePacketBuilderAgent._looks_truncated(sentence) or SlidePacketBuilderAgent._looks_like_heading_noise(sentence):
                continue
            if any(term in lower for term in anchors):
                facts.append(ContentQualityAgent._sentence_safe_truncate(sentence, 240))
        return SlidePacketBuilderAgent._dedupe_by_overlap(facts)[:8]

    @staticmethod
    def _role_anchor_terms(role: str) -> List[str]:
        by_role = {
            "mechanism": ["csem", "epfl", "encapsulant", "front glass", "ceramic", "hotspot", "print density", "relative efficiency"],
            "progression": ["trl", "technology readiness", "prototype", "level 5", "level 9", "commercial application"],
            "commercialization": ["swisspanel solar", "glas trösch", "swissbau", "certification", "supsi", "pv module manufacturer", "architects", "clients"],
            "dissemination": ["public talks", "non-scientific publications", "professional education", "building professionals", "general public"],
            "overview": ["knowledge transfer", "visual assessment", "commercial product", "coloured pv", "technology transfer"],
        }
        return by_role.get(role, [])

    @staticmethod
    def _role_anchor_check(role: str, facts: List[str]) -> Dict[str, Any] | None:
        critical_by_role = {
            "mechanism": ["csem", "epfl", "hslu", "ceramic", "hotspot", "print density", "relative efficiency"],
            "progression": ["trl", "level 5", "prototype", "level 9", "commercial application"],
            "commercialization": ["swisspanel solar", "glas trösch", "swissbau", "certification", "supsi", "manufacturer"],
            "dissemination": ["public talks", "non-scientific publications", "professional education", "building professionals"],
        }
        terms = critical_by_role.get(role, [])
        if not terms:
            return None
        available = []
        fact_text = " ".join(facts).lower()
        for term in terms:
            if term in fact_text:
                available.append(term)
        if not available:
            return None
        return {"kind": "role_anchors", "role": role, "items": available[:6], "min_hits": min(2, len(available))}

    @staticmethod
    def _merge_forced_role_facts(role: str, role_facts: List[str], ranked_facts: List[str]) -> List[str]:
        forced = []
        target_terms = SlidePacketBuilderAgent._role_anchor_terms(role)
        for fact in role_facts:
            lower = fact.lower()
            if any(term in lower for term in target_terms):
                forced.append(fact)
            if len(forced) >= 3:
                break
        return SlidePacketBuilderAgent._dedupe_by_overlap(forced + ranked_facts)

    @classmethod
    def _numbered_evidence_facts(cls, evidence: str, title: str, goal: str) -> List[str]:
        items = cls._extract_numbered_items(evidence)
        if not items:
            return []
        query_terms = cls._query_terms_for_list(f"{title} {goal}")
        ranked = []
        for item in items:
            text = item["text"]
            lower = text.lower()
            score = sum(2 for term in query_terms if term in lower)
            if score == 0 and any(term in lower for term in ["citizen science", "bürgerwissenschaft", "wissenschaft", "daten", "ethisch", "evaluierung"]):
                score = 1
            ranked.append((score, item["number"], text))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        max_score = ranked[0][0] if ranked else 0
        min_score = 4 if max_score >= 4 else 1
        selected = [row for row in ranked if row[0] >= min_score][:4]
        if len(selected) < 3 and len(items) <= 10 and max_score < 4:
            selected = [row for row in ranked if row[0] > 0][:4] or ranked[:4]
        facts = []
        for _, number, text in selected:
            facts.append(f"Principle {number}: {text}")
        return facts

    @staticmethod
    def _extract_numbered_items(evidence: str) -> List[Dict[str, Any]]:
        text = re.sub(r"--- Page\s+\d+\s+(?:structured\s+)?evidence ---", "\n", evidence)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
        text = re.sub(r"\*(?:Figure|Table|Fig\.?|Bảng|Hình)[:\s]+[^*]+\*", " ", text, flags=re.IGNORECASE)
        pattern = re.compile(r"(?ms)(?:^|\n|\s)(\d{1,2})\.\s+(.+?)(?=(?:\n|\s)\d{1,2}\.\s+|(?:\n|\s)!\[|\n\s*---|\Z)")
        items = []
        seen = set()
        for number, body in pattern.findall(text):
            clean = re.sub(r"\s+", " ", body).strip()
            if len(clean) < 20:
                continue
            if SlidePacketBuilderAgent._looks_like_reference_item(clean):
                continue
            if SlidePacketBuilderAgent._looks_truncated(clean):
                continue
            if re.search(r"\.(?:jpeg|jpg|png|webp)|figure:", clean, flags=re.IGNORECASE):
                continue
            key = (int(number), clean.lower())
            if key in seen:
                continue
            seen.add(key)
            items.append({"number": int(number), "text": ContentQualityAgent._sentence_safe_truncate(clean, 700)})
        return items

    @staticmethod
    def _query_terms_for_list(text: str) -> List[str]:
        synonyms = {
            "data": ["data", "daten", "metadaten"],
            "sharing": ["sharing", "teilen", "zugänglich", "zuganglich", "öffentlich", "publicly"],
            "recognition": ["recognition", "acknowledg", "dank", "wertschätzung", "wertschaetzung"],
            "evaluation": ["evaluation", "evaluierung", "qualität", "quality", "wirkung", "impact"],
            "ethical": ["ethical", "ethische", "legal", "rechte", "urheberrechte", "vertraulichkeit"],
            "considerations": ["considerations", "aspekte", "verantwortlichkeiten"],
            "principles": ["principles", "prinzipien", "citizen", "science", "bürgerwissenschaft"],
            "practice": ["practice", "praxis"],
            "development": ["entwickelt", "arbeitsgruppe", "ecsa"],
        }
        base_terms = []
        for term in re.findall(r"[a-zA-ZÀ-ỹ0-9_]{4,}", text.lower()):
            base_terms.append(term)
            base_terms.extend(synonyms.get(term, []))
        result = []
        seen = set()
        for term in base_terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                result.append(key)
        return result[:40]

    @staticmethod
    def _looks_reference_heavy(evidence: str) -> bool:
        year_hits = len(re.findall(r"\b(?:19|20)\d{2}\b", evidence))
        citation_hits = len(re.findall(r"\b[A-Z][A-Za-zÀ-ỹ'’-]+(?:\s+et\s+al\.)?\s*\(\d{4}\)", evidence))
        reference_words = len(re.findall(r"\b(reference|references|study|research|evidence|review|case study|toolkit|bibliography|literature)\b", evidence, flags=re.IGNORECASE))
        return year_hits >= 4 and (citation_hits >= 2 or reference_words >= 4)

    @classmethod
    def _reference_evidence_facts(cls, evidence: str, title: str = "") -> List[str]:
        text = ContentQualityAgent._clean_evidence_text(evidence)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        title_terms = [
            term
            for term in re.findall(r"[A-Za-zÀ-ỹ0-9_]{4,}", title.lower())
            if term not in {"evidence", "references", "section", "content", "overview"}
        ]
        ranked = []
        for sentence in sentences:
            clean = re.sub(r"\s+", " ", sentence).strip()
            lower = clean.lower()
            if not clean or len(clean) < 30:
                continue
            if cls._looks_truncated(clean):
                continue
            if "assets/" in lower or "[block" in lower or "last retrieved" in lower:
                continue
            has_year = bool(re.search(r"\b(?:19|20)\d{2}\b", clean))
            has_signal = any(term in lower for term in ["evidence", "benefit", "impact", "study", "research", "review", "support", "effectiveness", "perception", "practice"])
            if not (has_year or has_signal):
                continue
            score = sum(2 for term in title_terms if term in lower)
            score += 2 if has_year else 0
            score += 1 if has_signal else 0
            ranked.append((score, ContentQualityAgent._sentence_safe_truncate(clean, 180)))
        ranked.sort(key=lambda item: (-item[0], len(item[1])))
        facts = []
        for _, sentence in ranked:
            if sentence not in facts:
                facts.append(sentence)
            if len(facts) >= 5:
                break
        return facts

    @staticmethod
    def _source_pages(evidence: str) -> List[int]:
        pages = []
        for match in re.finditer(r"--- Page\s+(\d+)\s+evidence ---", evidence):
            page = int(match.group(1))
            if page not in pages:
                pages.append(page)
        return pages

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        result = []
        seen = set()
        for item in items:
            key = re.sub(r"\s+", " ", item.strip().lower())
            if key and key not in seen:
                seen.add(key)
                result.append(item.strip())
        return result

    @staticmethod
    def _dedupe_coverage(items: List[str]) -> List[str]:
        result: List[str] = []
        index_by_key: Dict[str, int] = {}
        for item in items:
            number_match = re.match(r"Principle\s+(\d+):", item, flags=re.IGNORECASE)
            key = f"principle:{number_match.group(1)}" if number_match else re.sub(r"\s+", " ", item.strip().lower())
            if not key:
                continue
            clean = item.strip()
            if key in index_by_key:
                idx = index_by_key[key]
                if len(clean) > len(result[idx]):
                    result[idx] = clean
                continue
            index_by_key[key] = len(result)
            result.append(clean)
        return result

    def _prioritize_facts(self, spec: Slide, role: str, facts: List[str], used_fact_keys: set[str]) -> List[str]:
        title_goal = f"{spec.slide_title} {spec.goal}".lower()
        ranked = []
        for idx, fact in enumerate(facts):
            clean = self._clean_fact(fact)
            if not clean or self._looks_truncated(clean):
                continue
            lower = clean.lower()
            score = 0
            score += self._role_score(role, lower)
            score += sum(1 for term in re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", title_goal) if term.lower() in lower)
            score += 3 if re.search(r"\d|[A-Z]{2,}", clean) else 0
            if self._is_role_critical(role, lower):
                score += 8
            if self._fact_key(clean) in used_fact_keys:
                score -= 2 if self._is_role_critical(role, lower) else 5
            ranked.append((score, idx, clean))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        return self._mmr_select(ranked, limit=10)

    @staticmethod
    def _role_score(role: str, fact_lower: str) -> int:
        terms_by_role = {
            "overview": ["knowledge transfer", "assessment", "theme", "concept", "commercial product"],
            "dissemination": ["outreach", "public talks", "publication", "education", "audience", "building professionals", "general public"],
            "mechanism": ["csem", "epfl", "front glass", "encapsulant", "printing", "ceramic", "technology", "colour", "color", "hotspot", "efficiency", "print density", "design"],
            "progression": ["trl", "technology readiness", "prototype", "level 5", "level 9", "commercial application"],
            "commercialization": ["üserhuus", "glas trösch", "swisspanel solar", "swissbau", "certification", "supsi", "manufacturer"],
            "implication": ["application", "standard", "compliance", "impact", "integration"],
        }
        return sum(3 for term in terms_by_role.get(role, []) if term in fact_lower)

    @staticmethod
    def _is_role_critical(role: str, fact_lower: str) -> bool:
        return any(term in fact_lower for term in SlidePacketBuilderAgent._role_anchor_terms(role))

    @staticmethod
    def _mmr_select(ranked: List[tuple[int, int, str]], limit: int) -> List[str]:
        selected: List[str] = []
        candidates = [(score, idx, clean) for score, idx, clean in ranked if clean]
        while candidates and len(selected) < limit:
            best_pos = 0
            best_value = None
            for pos, (score, idx, clean) in enumerate(candidates):
                diversity_penalty = max((SlidePacketBuilderAgent._token_overlap(clean, item) for item in selected), default=0.0)
                value = score - 6.0 * diversity_penalty - idx * 0.001
                if best_value is None or value > best_value:
                    best_value = value
                    best_pos = pos
            _, _, chosen = candidates.pop(best_pos)
            if not any(SlidePacketBuilderAgent._token_overlap(chosen, item) >= 0.78 for item in selected):
                selected.append(chosen)
        return selected

    @staticmethod
    def _token_overlap(left: str, right: str) -> float:
        left_tokens = set(re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", left.lower()))
        right_tokens = set(re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", right.lower()))
        if not left_tokens or not right_tokens:
            left_cjk = set(re.findall(r"[\u4e00-\u9fff]", left))
            right_cjk = set(re.findall(r"[\u4e00-\u9fff]", right))
            return len(left_cjk & right_cjk) / min(len(left_cjk), len(right_cjk)) if left_cjk and right_cjk else 0.0
        return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))

    @staticmethod
    def _clean_fact(fact: str) -> str:
        clean = re.sub(r"\s+", " ", str(fact or "")).strip(" ;:-")
        clean = re.sub(r"--- Page\s+\d+\s+(?:structured\s+)?evidence ---.*$", "", clean).strip()
        if SlidePacketBuilderAgent._looks_like_heading_noise(clean) or SlidePacketBuilderAgent._looks_like_fragment(clean):
            return ""
        return ContentQualityAgent._sentence_safe_truncate(clean, 220)

    @staticmethod
    def _fact_key(fact: str) -> str:
        principle = re.match(r"\s*principle\s+(\d+)\s*:", fact, flags=re.IGNORECASE)
        if principle:
            return f"principle:{principle.group(1)}"
        tokens = [token for token in re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", fact.lower()) if token not in {"through", "using", "which", "with", "from", "this", "that"}]
        if not tokens:
            cjk = "".join(re.findall(r"[\u4e00-\u9fff]", fact))
            if cjk:
                return cjk[:24]
        return " ".join(tokens[:8])

    @staticmethod
    def _looks_truncated(text: str) -> bool:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if not clean:
            return True
        if re.search(r"\b(?:using|with|by|to|from|into|of|for|and|or|the|a|an)\s+[A-Za-z]\.?$", clean):
            return True
        if "--- Page" in clean:
            return True
        if SlidePacketBuilderAgent._looks_like_fragment(clean):
            return True
        return False

    @staticmethod
    def _looks_like_heading_noise(text: str) -> bool:
        lower = text.lower()
        if "**key words:**" in lower or " key words:" in lower:
            return True
        if lower.startswith(("references ", "table of content", "slide ")):
            return True
        if re.fullmatch(r"(?:[A-Z][A-Za-zÀ-ỹ0-9&/()'’.-]+\s*){1,8}", text.strip()):
            return True
        heading_markers = [" key words:", " target audience:", " patent and trademark", " references "]
        return any(marker in f" {lower}" for marker in heading_markers) and len(text.split()) < 18

    @staticmethod
    def _looks_like_fragment(text: str) -> bool:
        lower = text.strip().lower()
        if len(re.findall(r"[\u4e00-\u9fff]", text)) >= 8:
            return False
        if text.strip() and text.strip()[0].islower():
            return True
        if re.match(r"^(which|and|or|but|while|through|leading|resulting|providing|financially|supported by|accompanied by)\b", lower):
            return True
        if len(text.split()) < 5:
            return True
        return False

    @staticmethod
    def _candidate_matches_role(text: str, role: str) -> bool:
        lower = text.lower()
        if role in {"overview", "supporting_detail"}:
            return any(term in lower for term in ["knowledge transfer", "concept", "product", "assessment", "developed", "resulted", "application"])
        return SlidePacketBuilderAgent._role_score(role, lower) > 0

    @staticmethod
    def _dedupe_by_overlap(items: List[str]) -> List[str]:
        result: List[str] = []
        seen_keys: set[str] = set()
        for item in items:
            clean = re.sub(r"\s+", " ", str(item or "")).strip()
            if not clean:
                continue
            key = SlidePacketBuilderAgent._fact_key(clean)
            if key in seen_keys:
                continue
            if key.startswith("principle:"):
                seen_keys.add(key)
                result.append(clean)
                continue
            clean_l = clean.lower()
            duplicate = False
            for existing in result:
                existing_l = existing.lower()
                if clean_l in existing_l or existing_l in clean_l:
                    duplicate = True
                    break
                left = set(re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", clean_l))
                right = set(re.findall(r"[a-zA-ZÀ-ỹ0-9]{4,}", existing_l))
                if left and right and len(left & right) / min(len(left), len(right)) >= 0.75:
                    duplicate = True
                    break
            if duplicate:
                continue
            seen_keys.add(key)
            result.append(clean)
        return result

    @staticmethod
    def _safe_evidence(evidence: str) -> str:
        blocks = []
        evidence = evidence or ""
        parts = re.split(r"(--- Page\s+\d+\s+evidence ---)", evidence)
        for idx in range(1, len(parts), 2):
            header = parts[idx].strip()
            body = parts[idx + 1] if idx + 1 < len(parts) else ""
            clean_body = ContentQualityAgent._clean_evidence_text(body)
            blocks.append(f"{header}\n{ContentQualityAgent._sentence_safe_truncate(clean_body, 2400)}")
        if blocks:
            return "\n\n".join(blocks)
        clean = ContentQualityAgent._clean_evidence_text(evidence)
        return ContentQualityAgent._sentence_safe_truncate(clean, SlidePacketBuilderAgent.MAX_EVIDENCE_CHARS)

    @staticmethod
    def _empty_slide(spec: Slide):
        from src.models.slide import SlideContent
        return SlideContent(slide=spec, content=[])
