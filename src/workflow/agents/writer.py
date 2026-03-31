from src.utils.llm import chat
from typing import Dict, Optional, List
import json
import re
from src.utils.parse_llm_response import parse_json_response
from dataclasses import asdict
from collections import OrderedDict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide


class WriterAgent:
    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list, temperature: float = 0.4, max_tokens: int = None) -> str:
        return chat(self.model, messages, temperature=temperature, max_tokens=max_tokens)

    def _extract_relevant_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        return full_text if len(full_text) <= 150000 else full_text[:150000]

    def slide_type_example(self, slide_type: str) -> str:
        content = """
{{
  "content": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"]
}}
"""
        two_sub_contents = """
{{
  "content": {
    "Sub Content 1 Title": ["Point 1", "Point 2", "Point 3"],
    "Sub Content 2 Title": ["Point 1", "Point 2", "Point 3"]
  }
}}
"""
        comparison = """
{{
  "content": "A markdown table generated from the document summarizes the two comparable entities."
}}
"""
        mapping = {
            "content": content,
            "have_table": content,
            "have_formula": content,
            "two_sub_contents": two_sub_contents,
            "comparison": comparison,
        }
        return mapping.get(slide_type, content)

    def build_system_prompt(self, slide_type: str) -> str:
        example_slide = self.slide_type_example(slide_type)
        return f"""# ROLE 
You are an expert lecture slide writer specializing in engaging,
pedagogically clear slides derived from structured academic material.

# TASK 
Your task is to generate ONE lecture slide based on the Slide Description provided.
Preserve the tone and structure of the source material.

# CORE PRINCIPLE — PRESERVE SOURCE IDENTITY
The slide must preserve the meaning, tone, and technical content
of the source without rewriting it into generic textbook language.

# CONTENT SCOPE
The slide must stay strictly within the scope of the Slide Description.
Do not introduce new concepts.

# SLIDE CONSTRUCTION RULES
- Follow the language, tone, and style of the source material.
- Stay strictly within the scope of the Slide Description.
- Write 3–6 bullet points, each 5–20 words.
- Preserve vivid phrasing, examples, or questions when possible.
- Use proper LaTeX for any mathematical expression.

# OTHER IMPORTANT RULE: MATHEMATICS & NOTATION
- All mathematical expressions are wrapped in LaTeX delimiters.
  - Inline math uses $...$
  - Display math uses $$...$$
- Correct LaTeX commands are used consistently:
  - Trigonometric functions: $\\sin$, $\\cos$, $\\tan$
  - Greek letters: $\\alpha$, $\\beta$, $\\pi$
  - Fractions: $\\frac{{a}}{{b}}$
  - Superscripts: $x^2$, $\\sin^2 x$
  - Subscripts: $x_1$, $a_n$
  - Symbols: $\\neq$, $\\leq$, $\\geq$, $\\pm$, $\\infty$
- Plain-text mathematical notation is never used.

# OUTPUT FORMAT
Return ONLY valid JSON:
{example_slide}
"""

    def draft_a_slide(
        self,
        slide_spec: Slide,
        context: DocumentContext,
        parent_relevant_context: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> SlideContent:
        text_excerpt = self._extract_relevant_text(context)
        slide_type_str = slide_spec.slide_type.value if hasattr(slide_spec.slide_type, 'value') else str(slide_spec.slide_type)
        system_prompt = self.build_system_prompt(slide_type_str)

        spec_dict = asdict(slide_spec)
        if hasattr(spec_dict.get("slide_type"), "value"):
            spec_dict["slide_type"] = spec_dict["slide_type"].value
        spec_json = json.dumps(spec_dict, ensure_ascii=False, indent=2)

        user_prompt = f"""
Full source material excerpt: {text_excerpt}
Parent slide content: {parent_relevant_context}
Some feedback for improvement: {feedback}
Slide description: {spec_json}
"""
        content = self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=16000,
        )
        data = self._parse_json_response(content)
        return SlideContent(slide=slide_spec, content=data.get('content', []))

    def draft_slide_from_outline(
        self,
        outline_md: str,
        context: DocumentContext,
        slide_specs: List[Slide],
        feedback: Optional[str] = None,
    ) -> List[SlideContent]:
        _, outline_numbered_md = self.outline_md_to_number(outline_md)
        slides_content = []

        for spec in slide_specs:
            section = self._find_section_by_title(spec.slide_title, outline_numbered_md)
            parent_relevant_context = self.get_relevant_context(section, outline_numbered_md, slides_content)
            slides_content.append(
                self.draft_a_slide(
                    slide_spec=spec,
                    context=context,
                    parent_relevant_context=parent_relevant_context,
                    feedback=feedback,
                )
            )
        return slides_content

    def _find_section_by_title(self, slide_title: str, outline_numbered_md: str) -> str:
        for line in outline_numbered_md.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                title_part = parts[1].strip()
                if title_part.lower() == slide_title.lower():
                    return line
        return slide_title

    def get_relevant_context(self, section_key: str, outline_numbered_md: str, slides_content: List[SlideContent]) -> str:
        lines = [line.rstrip() for line in outline_numbered_md.splitlines() if line.strip()]
        pattern = re.compile(r'^([\d.]+)\s+(.*)$')

        all_sections = []
        current_level1 = None
        sections_after_level1 = []

        for line in lines:
            match = pattern.match(line)
            if not match:
                continue
            numbering = match.group(1)
            level = numbering.count('.')
            section_name = line.strip()

            if section_name == section_key:
                all_sections = ([current_level1] + sections_after_level1) if current_level1 else sections_after_level1
                break

            if level == 1:
                current_level1 = section_name
                sections_after_level1 = []
            else:
                sections_after_level1.append(section_name)

        if not all_sections:
            return ""
        return "Previous sections covered: " + ", ".join(all_sections)

    @classmethod
    def outline_md_to_number(cls, outline_md: str) -> tuple[dict, str]:
        lines = [line.rstrip() for line in outline_md.splitlines() if line.strip()]
        pattern = re.compile(r'^(#+)\s+(.*)$')

        stack = []
        root = OrderedDict()
        counters = []
        numbered_lines = []

        for line in lines:
            match = pattern.match(line)
            if not match:
                continue

            level = len(match.group(1))
            title = match.group(2).strip()

            while len(counters) < level:
                counters.append(0)
            while len(counters) > level:
                counters.pop()

            counters[-1] += 1
            counters[level - 1 + 1:] = []

            number = ".".join(str(c) for c in counters) + "."
            key = f"{number} {title}"
            numbered_lines.append(f"{number} {title}")

            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                root[key] = -1
                stack.append((level, root, key))
            else:
                parent_dict = stack[-1][1][stack[-1][2]]
                if parent_dict == -1:
                    parent_dict = OrderedDict()
                    stack[-1][1][stack[-1][2]] = parent_dict
                parent_dict[key] = -1
                stack.append((level, parent_dict, key))

        return root, "\n".join(numbered_lines)

    def _parse_json_response(self, content: str) -> Dict:
        invoke_fn = lambda msgs: type('R', (), {'content': self._chat(msgs)})()
        return parse_json_response(content, invoke_fn, expect_list=False)
