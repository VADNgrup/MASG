from src.utils.llm import chat
from typing import Dict, Any, List, Optional
import json
import re
from src.utils.parse_llm_response import parse_json_response
from src.models.context import DocumentContext
from src.models.slide import Slide, Table, SlideType

class PlanSpecerAgent:
    MAX_FULL_TEXT_LENGTH = 10000
    MAX_RETRIES = 3

    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list) -> str:
        return chat(self.model, messages, temperature=0.3, max_tokens=16000)

    @staticmethod
    def outline_md_to_number(outline_md: str) -> str:
        lines = outline_md.splitlines()
        counters: List[int] = []
        result_lines: List[str] = []
        for line in lines:
            match = re.match('^(#+)\\s+(.*)', line.strip())
            if not match:
                if line.strip():
                    result_lines.append(line)
                continue
            hashes = match.group(1)
            title = match.group(2)
            depth = len(hashes)
            if depth > len(counters):
                while len(counters) < depth:
                    counters.append(0)
            else:
                counters = counters[:depth]
            counters[-1] += 1
            number_str = '.'.join((str(c) for c in counters))
            if depth == 1:
                result_lines.append(f'{number_str}. {title}')
            else:
                result_lines.append(f'{number_str} {title}')
        return '\n'.join(result_lines)

    @staticmethod
    def _extract_expected_titles(numbered_outline: str) -> List[str]:
        titles = []
        for line in numbered_outline.splitlines():
            stripped = line.strip()
            if re.match('^\\d[\\d.]*[\\. ]', stripped):
                titles.append(stripped)
        return titles

    @staticmethod
    def _normalize_title(title: str) -> str:
        return re.sub('\\s+', ' ', title.strip().lower())

    @classmethod
    def _find_missing_titles(cls, raw_specs: List[Dict], expected_titles: List[str]) -> List[str]:

        def prefix_of(title: str) -> str:
            m = re.match('^([\\d.]+)', title.strip())
            return m.group(1).rstrip('.') if m else ''
        returned_prefixes = {prefix_of(d.get('slide_title', '')) for d in raw_specs if isinstance(d, dict)}
        missing = []
        for expected in expected_titles:
            if prefix_of(expected) not in returned_prefixes:
                missing.append(expected)
        return missing

    def _build_prompt(self, numbered_outline: str, full_text: str, context: DocumentContext) -> str:
        schema_example = '{\n  "slide_title": "<title from the heading, preserving its number prefix>",\n  "slide_type": "<one of: content, have_table, have_formula, comparison, two_sub_contents>",\n  "goal": "<1-2 sentence goal describing what this slide should convey>",\n  "table": {"table_markdown": "<markdown table string>", "table_caption": "<caption>"} or null,\n  "latex_block_formula": "<LaTeX block formula string>" or null\n}'
        return f'\n# ROLE\nYou are a lecture slide specification architect.\n\n# TASK\nGiven the FULL numbered lecture outline and the source document text, produce a JSON array\nof slide specifications — one object per heading line (both major `1.` and sub `1.1`, `1.1.1`, etc.).\nEvery heading in the outline MUST have exactly ONE corresponding JSON object.\n\n# INPUT\n## Full Numbered Outline\n{numbered_outline}\n\n## Source Document (truncated)\n{full_text}\n\n## Tables extracted from document\n{context.tables}\n\n# IMPORTANT CONSTRAINTS\n1. `slide_type` must be one of: "content", "have_table", "have_formula", "comparison", "two_sub_contents".\n2. Use "have_table" ONLY if the source document contains a table supporting this slide.\n   If so, include `table` with the markdown and caption. Otherwise set `table` to null.\n   2.1. Prioritize extracting the tables mentioned in the document.\n   2.2. Only tables with more than 2 rows and 2 columns. Smaller tables → use "content".\n3. Use "have_formula" ONLY if the source document contains a block-level formula for this slide.\n   If so, include `latex_block_formula`. Otherwise set it to null.\n4. Use "comparison": `goal` must describe the two comparable entities briefly.\n5. Use "two_sub_contents": `goal` must describe the two distinct sub-topics shown side by side.\n6. Default to "content" when none of the above special types apply.\n\n# CRITICAL\n- `slide_title` MUST preserve the numbering prefix EXACTLY as it appears in the outline\n  (e.g. "1. Introduction", "1.1 Background", "2.1.3 Survey Design").\n- The output array MUST contain one entry for EVERY line in the outline above — no omissions.\n\n# EXAMPLE\n[\n  {{\n    "slide_title": "1. Introduction",\n    "slide_type": "content",\n    "goal": "Introduce the topic and motivate the study.",\n    "table": null,\n    "latex_block_formula": null\n  }},\n  {{\n    "slide_title": "1.1 Background",\n    "slide_type": "content",\n    "goal": "Describe the historical and theoretical background.",\n    "table": null,\n    "latex_block_formula": null\n  }},\n  {{\n    "slide_title": "2. Methods",\n    "slide_type": "have_table",\n    "goal": "Summarise the methodology used.",\n    "table": {{\n      "table_markdown": "| Col1 | Col2 |\\n|------|------|\\n| Val1 | Val2 |",\n      "table_caption": "Overview of methods"\n    }},\n    "latex_block_formula": null\n  }}\n]\n\n# OUTPUT FORMAT\nReturn ONLY a valid JSON array. Each element must follow this schema:\n[{schema_example}]\n'

    def _truncate_full_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        return full_text[:self.MAX_FULL_TEXT_LENGTH] if len(full_text) > self.MAX_FULL_TEXT_LENGTH else full_text

    def _parse_json_response(self, content: str) -> List[Dict]:
        invoke_fn = lambda msgs: type('R', (), {'content': self._chat(msgs)})()
        return parse_json_response(content, invoke_fn)

    @staticmethod
    def _dict_to_slide(d: Dict[str, Any]) -> Slide:
        slide_type_str = d.get('slide_type', 'content')
        try:
            slide_type = SlideType(slide_type_str)
        except ValueError:
            slide_type = SlideType.CONTENT
        table_data = d.get('table')
        table = None
        if table_data and isinstance(table_data, dict):
            table = Table(table_markdown=table_data.get('table_markdown', ''), table_caption=table_data.get('table_caption', ''))
        return Slide(slide_title=d.get('slide_title', ''), slide_type=slide_type, goal=d.get('goal', ''), table=table, latex_block_formula=d.get('latex_block_formula'))

    def specify(self, outline_md: str, context: DocumentContext) -> List[Slide]:
        full_text = self._truncate_full_text(context)
        numbered_outline = self.outline_md_to_number(outline_md)
        expected_titles = self._extract_expected_titles(numbered_outline)
        print(f'\n[PlanSpecer] Outline has {len(expected_titles)} heading(s) to spec.')
        last_raw_specs: List[Dict] = []
        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f'[PlanSpecer] Attempt {attempt}/{self.MAX_RETRIES} — calling LLM for full outline...')
            prompt = self._build_prompt(numbered_outline, full_text, context)
            raw_content = self._chat([{'role': 'user', 'content': prompt}])
            try:
                raw_specs = self._parse_json_response(raw_content)
            except Exception as e:
                print(f'[PlanSpecer] JSON parse error on attempt {attempt}: {e}')
                if attempt < self.MAX_RETRIES:
                    print('[PlanSpecer] Retrying...')
                continue
            if not isinstance(raw_specs, list):
                print(f'[PlanSpecer] ✗ Expected a JSON array, got {type(raw_specs).__name__}. Retrying...')
                continue
            last_raw_specs = raw_specs
            missing = self._find_missing_titles(raw_specs, expected_titles)
            if missing:
                print(f"[PlanSpecer] {len(missing)} heading(s) missing from output (e.g. {missing[:3]}{('...' if len(missing) > 3 else '')}).")
                if attempt < self.MAX_RETRIES:
                    print('[PlanSpecer] Retrying...')
                continue
            print(f'[PlanSpecer] All {len(raw_specs)} specs validated successfully.')
            return self._build_slide_list(raw_specs)
        print(f'[PlanSpecer] WARNING: reached max retries ({self.MAX_RETRIES}). Using last result with {len(last_raw_specs)} spec(s) — may be incomplete.')
        return self._build_slide_list(last_raw_specs)

    def _build_slide_list(self, raw_specs: List[Dict]) -> List[Slide]:
        all_specs = [self._dict_to_slide(d) for d in raw_specs]
        for (idx, slide) in enumerate(all_specs, start=1):
            slide.slide_number = idx
        print(f'[PlanSpecer] Total slide specs: {len(all_specs)}')
        return all_specs