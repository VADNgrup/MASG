import json
from typing import Any, Dict, List

from src.models.slide import SlideContent
from src.utils.llm import chat
from src.utils.parse_llm_response import parse_json_response
from src.workflow.agents.content_quality import ContentQualityAgent


class DirectBulletWriterAgent:
    BATCH_SIZE = 4
    MAX_OUTPUT_TOKENS = 1536
    PROMPT_TOKEN_BUDGET = 5600

    def __init__(self, model: str):
        self.model = model
        self.content_tools = ContentQualityAgent(model)

    def _chat(self, messages: list, max_tokens: int | None = None) -> str:
        return chat(self.model, messages, temperature=0.25, max_tokens=max_tokens or self.MAX_OUTPUT_TOKENS)

    def write(self, packets: List[Dict[str, Any]], slide_specs: List) -> List[SlideContent]:
        if not packets:
            return []
        spec_by_number = {spec.slide_number: spec for spec in slide_specs}
        results: List[SlideContent] = []
        for batch in self._chunks(packets, self.BATCH_SIZE):
            results.extend(self._write_batch(batch, spec_by_number))
        return results

    def _write_batch(self, packets: List[Dict[str, Any]], spec_by_number: Dict[int, Any]) -> List[SlideContent]:
        prompt = self._build_prompt(packets)
        if len(packets) > 1 and self._estimate_tokens(prompt) > self.PROMPT_TOKEN_BUDGET:
            midpoint = max(1, len(packets) // 2)
            return self._write_batch(packets[:midpoint], spec_by_number) + self._write_batch(packets[midpoint:], spec_by_number)
        max_tokens = self._output_budget(prompt, len(packets))
        raw = self._chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
        invoke_fn = lambda msgs: type("R", (), {"content": self._chat(msgs, max_tokens=max_tokens)})()
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

    @staticmethod
    def _build_prompt(packets: List[Dict[str, Any]]) -> str:
        prompt_packets = [DirectBulletWriterAgent._prompt_packet(packet) for packet in packets]
        return (
            "# ROLE\n"
            "You write final presentation bullets from source-grounded slide packets.\n\n"
            "# TASK\n"
            "For each packet, produce final slide content directly as 3 to 5 bullets.\n\n"
            "# NON-NEGOTIABLE RULES\n"
            "- Use ONLY facts supported by the packet evidence or required_facts.\n"
            "- Preserve every required_fact that fits the slide title.\n"
            "- Follow the packet role; do not turn every slide into the same overview.\n"
            "- If coverage_items are provided, cover several distinct items rather than repeating one generic theme.\n"
            "- If a source fact starts with labels like `Principle 1:`, `Step 2:`, or `Item 3:`, rewrite it as a natural presentation bullet instead of copying the label verbatim, unless the slide title explicitly asks for a numbered list.\n"
            "- Avoid repeating the same named entities or facts across neighboring slides unless the packet title requires them.\n"
            "- Do not introduce numbers that are not in required_facts/evidence.\n"
            "- Do not copy page headers, journal headers, figure labels, markdown headings, or source page numbers as facts.\n"
            "- Keep bullets concise but not vague.\n"
            "- Avoid generic bullets that could apply to any document; each bullet should contain a source-specific noun, number, method, action, result, or implication.\n"
            "- Preserve formulas and units exactly enough to be mathematically faithful.\n"
            "- For software workflow slides, keep each action as a clean action bullet.\n\n"
            "# SLIDE PACKETS\n"
            f"{json.dumps(prompt_packets, ensure_ascii=False, indent=2)}\n\n"
            "# OUTPUT\n"
            'Return ONLY a valid JSON array like [{"slide_number": 1, "content": ["bullet", "bullet", "bullet"]}].'
        )

    @staticmethod
    def _prompt_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
        keep = {
            "slide_number": packet.get("slide_number"),
            "slide_title": packet.get("slide_title"),
            "goal": packet.get("goal"),
            "intent": packet.get("intent"),
            "role": packet.get("role"),
            "coverage_mode": packet.get("coverage_mode"),
            "source_pages": packet.get("source_pages", []),
            "required_facts": packet.get("required_facts", [])[:8],
            "required_checks": packet.get("required_checks", [])[:4],
            "coverage_items": packet.get("coverage_items", [])[:6],
        }
        if packet.get("table"):
            keep["table"] = packet.get("table")
        if packet.get("latex_block_formula"):
            keep["latex_block_formula"] = packet.get("latex_block_formula")
        evidence_limit = 1600 if packet.get("coverage_mode") == "list_coverage" else 1200
        evidence = str(packet.get("evidence") or "")
        if evidence:
            keep["evidence_excerpt"] = ContentQualityAgent._sentence_safe_truncate(evidence, evidence_limit)
        return keep

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, int(len(text) / 3.6))

    def _output_budget(self, prompt: str, slide_count: int) -> int:
        prompt_tokens = self._estimate_tokens(prompt)
        remaining = max(512, 7900 - prompt_tokens)
        per_slide = max(384, slide_count * 320)
        return min(self.MAX_OUTPUT_TOKENS, remaining, per_slide)

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
        if self._too_generic(bullets, packet):
            bullets = self._fallback_bullets(packet, spec) + bullets
        return self._dedupe(bullets)[:5]

    def _fallback_bullets(self, packet: Dict[str, Any], spec: Any) -> List[str]:
        evidence = packet.get("evidence", "")
        deterministic = self.content_tools._deterministic_content(self._empty_slide(spec), evidence, packet)
        if deterministic:
            return deterministic
        facts = [fact for fact in packet.get("required_facts", []) if isinstance(fact, str)]
        if facts:
            return [self.content_tools._clean_bullet(fact) for fact in facts[:5]]
        return self.content_tools._fallback_items(evidence)[:5]

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        return ContentQualityAgent._dedupe_bullets(items)

    def _too_generic(self, bullets: List[str], packet: Dict[str, Any]) -> bool:
        if not bullets:
            return True
        if packet.get("coverage_mode") in {"list_coverage", "reference_synthesis"}:
            return False
        generic_count = sum(1 for bullet in bullets if self.content_tools._is_generic_bullet(bullet))
        return generic_count >= max(2, len(bullets) // 2 + 1)

    @staticmethod
    def _empty_slide(spec):
        from src.models.slide import SlideContent
        return SlideContent(slide=spec, content=[])

    @staticmethod
    def _chunks(items: List, size: int) -> List[List]:
        return [items[i : i + size] for i in range(0, len(items), size)]
