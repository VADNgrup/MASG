from dataclasses import asdict
import re
from typing import Any, Dict, List

from src.models.context import DocumentContext
from src.models.slide import Slide
from src.workflow.agents.content_quality import ContentQualityAgent


class SlidePacketBuilderAgent:
    MAX_EVIDENCE_CHARS = 1800

    def __init__(self, model: str):
        self.content_tools = ContentQualityAgent(model)

    def build_packets(self, slide_specs: List[Slide], context: DocumentContext) -> List[Dict[str, Any]]:
        packets = []
        for spec in slide_specs:
            evidence = self.content_tools._retrieve_evidence(context, self._empty_slide(spec))
            intent = self._infer_intent(spec)
            facts = self._required_facts(spec, evidence, intent)
            checks = self._required_checks(spec, evidence, facts, intent)
            packet = {
                "slide_number": spec.slide_number,
                "slide_title": spec.slide_title,
                "slide_type": spec.slide_type.value if hasattr(spec.slide_type, "value") else str(spec.slide_type),
                "goal": spec.goal,
                "intent": intent,
                "source_pages": self._source_pages(evidence),
                "required_facts": facts,
                "required_checks": checks,
                "evidence": evidence[: self.MAX_EVIDENCE_CHARS],
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
        if any(word in scope for word in ["software", "workflow", "input", "saving", "tool", "procedure"]):
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
        text = re.sub(r"\s+", " ", evidence)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        ranked = []
        for sentence in sentences:
            clean = sentence.strip()
            lower = clean.lower()
            if not clean or clean.startswith("---") or "dagon university research journal" in lower:
                continue
            score = sum(1 for term in title_terms if term in lower)
            if score == 0 and re.search(r"objective formula|result values|slack values|constraint:", lower):
                continue
            if score > 0 or re.search(r"\d|objective|constraint|software|application|model|optimal|feasible", lower):
                ranked.append((score, clean[:160]))
        ranked.sort(key=lambda item: (-item[0], len(item[1])))
        for _, fact in ranked:
            if fact not in facts:
                facts.append(fact)
            if len(facts) >= 4:
                break
        return facts

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
            if re.search(r"\.(?:jpeg|jpg|png|webp)|figure:", clean, flags=re.IGNORECASE):
                continue
            key = (int(number), clean.lower())
            if key in seen:
                continue
            seen.add(key)
            items.append({"number": int(number), "text": clean[:700]})
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
    def _empty_slide(spec: Slide):
        from src.models.slide import SlideContent
        return SlideContent(slide=spec, content=[])
