import llm_extension

from langchain_openai import ChatOpenAI
from typing import Dict, Optional, List
import json
import re
from src.utils.parse_llm_response import parse_json_response
from dataclasses import asdict
from collections import OrderedDict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.utils.config import config

class WriterAgent:
    def __init__(self, model):
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
        self.model = model
    
    def _extract_relevant_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        
        if len(full_text) <= 150000:
            return full_text
        else:
            return full_text[:150000]
    
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
        feedback: Optional[str] = None
    ) -> SlideContent:
        text_excerpt = self._extract_relevant_text(context)
        
        # Get slide_type as string
        slide_type_str = slide_spec.slide_type.value if hasattr(slide_spec.slide_type, 'value') else str(slide_spec.slide_type)
        
        system_prompt = self.build_system_prompt(slide_type_str)
        
        # Serialize spec to JSON string for the prompt
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
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        data = self._parse_json_response(response.content)
        return SlideContent(slide=slide_spec, content=data.get('content', []))

    def draft_slide_from_outline(
        self,
        outline_md: str,
        context: DocumentContext,
        slide_specs: List[Slide],
        feedback: Optional[str] = None,
    ) -> List[SlideContent]:
    
        # Convert markdown outline to numbered markdown outline
        _, outline_numbered_md = self.outline_md_to_number(outline_md)
        slides_content = []

        for spec in slide_specs:
            # Use spec's slide_title to find relevant context from outline
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
        """
        Extract section titles that appear before the given section_key,
        stopping when reaching a level-1 section.
        
        Args:
            section_key: The target section key (e.g., "1.1.2. subsubsection 2 name")
            outline_numbered_md: Numbered markdown outline string (without '#' symbols)
            slides_content: List of SlideContent objects created so far
            
        Returns:
            String containing relevant section titles (NOT full content) for context
            
        Example:
            If section_key = "1.1.2. subsubsection 2 name", returns:
            "Previous sections: 1. Section 1 name, 1.1. subsection 1 name, 1.1.1. subsubsection 1 name"
            
            If section_key = "2. Section 2 name", returns: ""
        """
        lines = [line.rstrip() for line in outline_numbered_md.splitlines() if line.strip()]
        # Pattern to match numbered sections like "1. Title" or "1.1.2. Title"
        pattern = re.compile(r'^([\d.]+)\s+(.*)$')
        
        all_sections = []
        current_level1 = None
        sections_after_level1 = []
        
        for line in lines:
            match = pattern.match(line)
            if not match:
                continue
            
            # Count dots to determine level: "1." = 1 dot = level 1, "1.1." = 2 dots = level 2
            numbering = match.group(1)
            level = numbering.count('.')
            section_name = line.strip()  # Use the full line as section name
            
            # Check if this is our target section
            if section_name == section_key:
                # Found the target, combine level-1 section with all sections after it
                if current_level1:
                    all_sections = [current_level1] + sections_after_level1
                else:
                    all_sections = sections_after_level1
                break
            
            # Track sections
            if level == 1:
                # New level-1 section found, reset tracking
                current_level1 = section_name
                sections_after_level1 = []
            else:
                # This is a subsection, add it to the list
                sections_after_level1.append(section_name)
        
        relevant_sections = all_sections
        
        if len(relevant_sections) == 0: 
            return ""
        else:
            # Return ONLY section titles, not full content
            # This prevents LLM from copying parent slide content
            return "Previous sections covered: " + ", ".join(relevant_sections)
    
    @classmethod    
    def outline_md_to_number(cls, outline_md: str) -> tuple[dict, str]:
        lines = [line.rstrip() for line in outline_md.splitlines() if line.strip()]
        pattern = re.compile(r'^(#+)\s+(.*)$')

        # Stack holds tuples: (level, dict_ref, index_path)
        # index_path = [1, 2, 1]  -> "1.2.1."
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

            # Adjust counters depth
            while len(counters) < level:
                counters.append(0)
            while len(counters) > level:
                counters.pop()

            counters[-1] += 1
            counters[level - 1 + 1:] = []

            number = ".".join(str(c) for c in counters) + "."
            key = f"{number} {title}"
            
            # Build numbered markdown line (without # prefix)
            numbered_lines.append(f"{number} {title}")

            # Pop stack until parent level
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
        
        numbered_md = "\n".join(numbered_lines)
        return root, numbered_md

    def _parse_json_response(self, response_content: str) -> Dict:
        return parse_json_response(response_content, self.llm.invoke, expect_list=False)
