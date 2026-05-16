import json
from typing import Any, Dict, List

from src.models.slide import SlideContent
from src.utils.llm import chat
from src.utils.parse_llm_response import parse_json_response
from src.workflow.agents.content_quality import ContentQualityAgent


class DirectBulletWriterAgent:
    BATCH_SIZE = 4
    MAX_OUTPUT_TOKENS = 2048

    def __init__(self, model: str):
        self.model = model
        self.content_tools = ContentQualityAgent(model)

    def _chat(self, messages: list) -> str:
        return chat(self.model, messages, temperature=0.25, max_tokens=self.MAX_OUTPUT_TOKENS)

    def write(self, packets: List[Dict[str, Any]], slide_specs: List) -> List[SlideContent]:
        if not packets:
            return []
        spec_by_number = {spec.slide_number: spec for spec in slide_specs}
        results: List[SlideContent] = []
        for batch in self._chunks(packets, self.BATCH_SIZE):
            results.extend(self._write_batch(batch, spec_by_number))
        return results

    def _write_batch(self, packets: List[Dict[str, Any]], spec_by_number: Dict[int, Any]) -> List[SlideContent]:
        prompt = (
            "# ROLE\n"
            "You write final presentation bullets from source-grounded slide packets.\n\n"
            "# TASK\n"
            "For each packet, produce final slide content directly as 3 to 5 bullets.\n\n"
            "# NON-NEGOTIABLE RULES\n"
            "- Use ONLY facts supported by the packet evidence or required_facts.\n"
            "- Preserve every required_fact that fits the slide title.\n"
            "- Do not introduce numbers that are not in required_facts/evidence.\n"
            "- Do not copy page headers, journal headers, figure labels, markdown headings, or source page numbers as facts.\n"
            "- Keep bullets concise but not vague.\n"
            "- Preserve formulas and units exactly enough to be mathematically faithful.\n"
            "- For software workflow slides, keep each action as a clean action bullet.\n\n"
            "# SLIDE PACKETS\n"
            f"{json.dumps(packets, ensure_ascii=False, indent=2)}\n\n"
            "# OUTPUT\n"
            'Return ONLY a valid JSON array like [{"slide_number": 1, "content": ["bullet", "bullet", "bullet"]}].'
        )
        raw = self._chat([{"role": "user", "content": prompt}])
        invoke_fn = lambda msgs: type("R", (), {"content": self._chat(msgs)})()
        data = parse_json_response(raw, invoke_fn, expect_list=True)
        by_number: Dict[int, Any] = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("slide_number") is not None:
                    by_number[int(item["slide_number"])] = item.get("content", [])
        slides: List[SlideContent] = []
        for packet in packets:
            num = int(packet["slide_number"])
            spec = spec_by_number[num]
            content = self._normalise_content(by_number.get(num, []), packet, spec)
            slides.append(SlideContent(slide=spec, content=content))
        return slides

    def _normalise_content(self, content: Any, packet: Dict[str, Any], spec: Any) -> List[str]:
        bullets = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    for line in item.splitlines():
                        clean = self.content_tools._clean_bullet(line)
                        if clean and not self.content_tools._is_bad_line(clean):
                            bullets.append(clean)
        elif isinstance(content, str):
            for line in content.splitlines():
                clean = self.content_tools._clean_bullet(line)
                if clean and not self.content_tools._is_bad_line(clean):
                    bullets.append(clean)
        if len(bullets) < 3:
            bullets.extend(self._fallback_bullets(packet, spec))
        return self._dedupe(bullets)[:5]

    def _fallback_bullets(self, packet: Dict[str, Any], spec: Any) -> List[str]:
        evidence = packet.get("evidence", "")
        deterministic = self.content_tools._deterministic_content(self._empty_slide(spec), evidence, packet)
        if deterministic:
            return deterministic
        facts = [fact for fact in packet.get("required_facts", []) if isinstance(fact, str)]
        if facts:
            return facts[:5]
        return self.content_tools._fallback_items(evidence)[:5]

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        result = []
        seen = set()
        for item in items:
            key = " ".join(item.lower().split())
            if key and key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @staticmethod
    def _empty_slide(spec):
        from src.models.slide import SlideContent
        return SlideContent(slide=spec, content=[])

    @staticmethod
    def _chunks(items: List, size: int) -> List[List]:
        return [items[i : i + size] for i in range(0, len(items), size)]
