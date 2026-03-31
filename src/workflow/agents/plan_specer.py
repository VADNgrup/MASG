from src.utils.llm import chat
from typing import Dict, Any, List, Optional
import json
import re
from src.utils.parse_llm_response import parse_json_response
from src.models.context import DocumentContext
from src.models.slide import Slide, Table, SlideType


class PlanSpecerAgent:
    """
    Intermediate agent between planner and writer.
    Converts the outline into a flat array of Slide JSON specifications using LLM.
    Each heading (both # and ##) produces one Slide spec.
    """

    MAX_FULL_TEXT_LENGTH = 10_000

    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list) -> str:
        return chat(self.model, messages, temperature=0.3, max_tokens=8000)

    @staticmethod
    def outline_md_to_number(outline_md: str) -> str:
        """
        Convert markdown headings (#, ##, ###, ...) into numbered format.

        Example:
            # Introduction          -> 1. Introduction
            ## Background           -> 1.1 Background
            ## Motivation           -> 1.2 Motivation
            # Methods               -> 2. Methods
            ## Data Collection      -> 2.1 Data Collection
            ### Survey Design       -> 2.1.1 Survey Design
        """
        lines = outline_md.splitlines()
        counters: List[int] = []
        result_lines: List[str] = []

        for line in lines:
            match = re.match(r'^(#+)\s+(.*)', line.strip())
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
            number_str = ".".join(str(c) for c in counters)
            if depth == 1:
                result_lines.append(f"{number_str}. {title}")
            else:
                result_lines.append(f"{number_str} {title}")

        return "\n".join(result_lines)

    def _split_outline_by_major_headings(self, numbered_outline: str) -> List[str]:
        lines = numbered_outline.splitlines()
        chunks: List[str] = []
        current_chunk_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            if re.match(r'^\d+\.\s+', stripped):
                if current_chunk_lines:
                    chunks.append("\n".join(current_chunk_lines))
                current_chunk_lines = [stripped]
            elif stripped:
                current_chunk_lines.append(stripped)

        if current_chunk_lines:
            chunks.append("\n".join(current_chunk_lines))

        return chunks

    def _truncate_full_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        return full_text[:self.MAX_FULL_TEXT_LENGTH] if len(full_text) > self.MAX_FULL_TEXT_LENGTH else full_text

    def _build_prompt(self, section_chunk: str, full_text: str, context: DocumentContext) -> str:
        schema_example = (
            '{\n'
            '  "slide_title": "<title from the heading>",\n'
            '  "slide_type": "<one of: content, have_table, have_formula, comparison, two_sub_contents>",\n'
            '  "goal": "<1-2 sentence goal describing what this slide should convey>",\n'
            '  "table": {"table_markdown": "<markdown table string> if slide_type is have_table", "table_caption": "<caption>"} or null,\n'
            '  "latex_block_formula": "<LaTeX block formula string> if slide_type is have_formula" or null\n'
            '}'
        )

        return f"""
# ROLE
You are a lecture slide specification architect.

# TASK
Given a section of a lecture outline and the source document text, produce a JSON array of slide specifications.
Each heading in the outline (including major `#` and sub `##` or sub of sub `###` etc.) must produce exactly ONE JSON object.

# INPUT
## Outline Section
{section_chunk}

## Source Document (truncated)
{full_text}

## List of Table extracted from document: 
{context.tables}

# IMPORTANT CONSTRAINTS
1. `slide_type` must be one of: "content", "have_table", "have_formula", "comparison", "two_sub_contents".
2. Use "have_table" ONLY if the source document contains a table supporting this slide. If so, include `table` with the markdown and caption. Otherwise set `table` to null.
2.1. Prioritize extracting the tables mentioned in the document. Note that the tables are organized in markdown format directly within the document.
2.2. For tables, only tables with more than 2 rows and 2 columns will be extracted. Tables that do not meet this condition will be represented as content.
3. Use "have_formula" ONLY if the source document contains a block-level formula supporting this slide. If so, include `latex_block_formula`. Otherwise set it to null.
4. Use "comparison", `goal` must describe briefly about two comparsion object.
5. Use "two_sub_contents", `goal` must describe briefly about two distinct sub-topics that should be shown side by side.
6. Default to "content" when none of the above special types apply.

# IMPORTANT
- The `slide_title` MUST preserve the numbering prefix exactly as it appears in the outline heading (e.g. "1. Introduction", "1.1 Background").

# EXAMPLE
## Only content:
{{
    "slide_title": "1. Title A",
    "slide_type": "content",
    "goal": "Goal A, Goal B",
    "table": null
    "latex_block_formula": null
}}
## Have table:
{{
    "slide_title": "1.1 Title A",
    "slide_type": "have_table",
    "goal": "Goal A, Goal B",
    "table": {{
        "table_markdown": "| Col1 | Col2 |\\n|------|------|\\n| Val1 | Val2 |",
        "table_caption": "Caption A"
    }},
    "latex_block_formula": null
}}
## Have formula:
{{
    "slide_title": "1.2 Title A",
    "slide_type": "have_formula",
    "goal": "Goal A, Goal B",
    "table": null
    "latex_block_formula": "\\\\frac{{a}}{{b}}"
}}
## Comparison:
{{
    "slide_title": "2. Title A",
    "slide_type": "comparison",
    "goal": "Refers to the comparable entities A and B.",
    "table": null
    "latex_block_formula": null
}}
## Two sub contents:
{{
    "slide_title": "2.1 Title A",
    "slide_type": "two_sub_contents",
    "goal": "Refers to the two sub-topics A and B.",
    "table": null
    "latex_block_formula": null
}}
# OUTPUT FORMAT
Return ONLY a valid JSON array. Each element must follow this schema:
[{schema_example}]
"""

    def _parse_json_response(self, content: str) -> List[Dict]:
        invoke_fn = lambda msgs: type('R', (), {'content': self._chat(msgs)})()
        return parse_json_response(content, invoke_fn)

    @staticmethod
    def _dict_to_slide(d: Dict[str, Any]) -> Slide:
        slide_type_str = d.get("slide_type", "content")
        try:
            slide_type = SlideType(slide_type_str)
        except ValueError:
            slide_type = SlideType.CONTENT

        table_data = d.get("table")
        table = None
        if table_data and isinstance(table_data, dict):
            table = Table(
                table_markdown=table_data.get("table_markdown", ""),
                table_caption=table_data.get("table_caption", ""),
            )

        return Slide(
            slide_title=d.get("slide_title", ""),
            slide_type=slide_type,
            goal=d.get("goal", ""),
            table=table,
            latex_block_formula=d.get("latex_block_formula"),
        )

    def specify(self, outline_md: str, context: DocumentContext) -> List[Slide]:
        """Convert the outline into a flat list of Slide specs."""
        full_text = self._truncate_full_text(context)
        numbered_outline = self.outline_md_to_number(outline_md)
        chunks = self._split_outline_by_major_headings(numbered_outline)

        all_specs: List[Slide] = []

        for i, chunk in enumerate(chunks):
            print(f"Specifying section {i + 1}/{len(chunks)}...")
            prompt = self._build_prompt(chunk, full_text, context)
            content = self._chat([{"role": "user", "content": prompt}])
            raw_specs = self._parse_json_response(content)
            all_specs.extend(self._dict_to_slide(d) for d in raw_specs)

        for idx, slide in enumerate(all_specs, start=1):
            slide.slide_number = idx

        print(f"Total slide specs generated: {len(all_specs)}")
        return all_specs
