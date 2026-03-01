import llm_extension

from langchain_openai import ChatOpenAI
from typing import Dict, Optional, List
import json
import re
from collections import OrderedDict
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.utils.config import config
from src.utils.latex_processor import process_slide_latex

class WriterAgent:
    def __init__(self, model: str = "gpt-4.1-nano"):
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
        self.model = model
    
    def _extract_relevant_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        
        if len(full_text) <= 150000:
            return full_text
        else:
            return full_text[:150000]
        
    
    def draft_a_slide(
        self, 
        section: str, 
        context: DocumentContext,
        parent_relevant_context: Optional[str] = None,
        slide_number: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> SlideContent:
        text_excerpt = self._extract_relevant_text(context)
        
        system_prompt = """
You are an expert lecture slide writer specializing in creating engaging, lively, and pedagogically sound slides from structured academic or technical material.
Your task is to generate ONE lecture slide that faithfully reflects the source material and elaborates on the given Parent Slide Content. The slide must preserve the original tone, energy, language style, and content structure of the source while remaining clear, engaging, and suitable for teaching.

CORE PRINCIPLE — PRESERVE SOURCE IDENTITY
- The slide preserves the original tone, energy, style, and language patterns of the source material.
- The slide does not sanitize, flatten, or rewrite the content into generic textbook language.
- All technical details, formulas, code snippets, and structured content are kept accurate and intact.

CONTENT SCOPE & CONTEXT (CRITICAL)
- The slide content strictly stays within the scope defined by the Parent Slide Content.
- The slide elaborates, clarifies, or exemplifies the Parent Slide Content without introducing new concepts.
- Logical continuity with previous slides is preserved.

MATHEMATICAL FORMULAS — STRICT LaTeX RULES
- All mathematical expressions are wrapped in LaTeX delimiters.
  - Inline math uses $...$
  - Display math uses $$...$$
- Correct LaTeX commands are used consistently:
  - Trigonometric functions: $\\sin$, $\\cos$, $\\tan$
  - Greek letters: $\\alpha$, $\\beta$, $\\pi$
  - Fractions: $\\frac{a}{b}$
  - Superscripts: $x^2$, $\\sin^2 x$
  - Subscripts: $x_1$, $a_n$
  - Symbols: $\\neq$, $\\leq$, $\\geq$, $\\pm$, $\\infty$
- Plain-text mathematical notation is never used.

SLIDE CONSTRUCTION RULES
- Language is the same as the source material.
- The title contains at most 8 words and captures the core idea and energy of the slide.
- The content contains 3–5 bullet points (maximum 6).
- Each bullet point contains approximately 5-12 words, adjusted for importance.
- Original phrasing, vivid examples, questions, or analogies are preserved whenever possible.
- Any bullet containing mathematics uses correct LaTeX formatting.

QUALITY CHECK BEFORE FINALIZING
- The slide strictly stays within the scope of the Parent Slide Content and introduces no unrelated information.
- The tone, energy, and language style are consistent with the source material.
- All mathematical expressions are correctly formatted in LaTeX.
- The content is clear, engaging, and non-generic.
- The slide logically follows previous slides and maintains narrative continuity.

Return ONLY valid JSON:
There are two types of slides: content slide and comparison slide.
1. With content slide: 
{{
  "slide_type": "content",
  "content": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"],
}}
2. With comparison slide: 
{{
  "slide_type": "comparison",
  "content": {
    "comparison_object_1_name": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"],
    "comparison_object_2_name": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"],
  }
}}
"""     
        user_prompt = f"""
Section: {section}
Full source material excerpt: {text_excerpt}
Parent slide content: {parent_relevant_context}
Some feedback for improvement: {feedback}

REMEMBER: ALL mathematical expressions MUST be wrapped in LaTeX $...$ or $$...$$ delimiters!""" 
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        data = self._parse_json_response(response.content)
        data = process_slide_latex(data)
        data['slide_title'] = section
        data['slide_number'] = slide_number
        return SlideContent(**data)

    def draft_slide_from_outline(self, outline_md: str, context: DocumentContext, feedback: Optional[str] = None) -> List[SlideContent]:
        """
        Convert outline markdown to slides by drafting each level 1 section.
        
        Args:
            outline_md: Markdown outline string with # headers
            context: DocumentContext containing source material
            
        Returns:
            List of SlideContent objects, one for each level 1 section
        """
        # Convert markdown outline to numbered markdown outline
        _, outline_numbered_md = self.outline_md_to_number(outline_md)
        # Split numbered markdown outline into sections
        outline_numbered_arr = outline_numbered_md.split("\n")
        slides_content = []
        slide_num = 1
        # Draft each section
        for section in outline_numbered_arr:
            parent_relevant_context = self.get_relevant_context(section, outline_numbered_md, slides_content)
            slides_content.append(self.draft_a_slide(section, context, parent_relevant_context, slide_num, feedback=feedback))
            slide_num += 1
        return slides_content

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
        """
        Convert a markdown outline (#, ##, ###, ...) into a numbered hierarchical dict
        and a numbered markdown string.
        Leaf nodes are marked with -1.

        INPUT
        # Section 1 name
        ## subsection 1 name
        ### subsubsection 1 name
        ### subsubsection 2 name
        ## subsection 2 name
        ### subsubsection 1 name
        ## subsection 3 name
        # Section 2 name
        # Section 3 name
        OUTPUT:
        output_dict = {
            "1. Section 1 name": {
                "1.1. subsection 1 name": {
                    "1.1.1. subsubsection 1 name": -1,
                    "1.1.2. subsubsection 2 name": -1
                },
                "1.2. subsection 2 name": {
                    "1.2.1. subsubsection 1 name": -1
                },
                "1.3. subsection 3 name": -1
            },
            "2. Section 2 name": -1,
            "3. Section 3 name": -1
        }
        output_md = 
        1. Section 1 name
        1.1. subsection 1 name
        1.1.1. subsubsection 1 name
        1.1.2. subsubsection 2 name
        1.2. subsection 2 name
        1.2.1. subsubsection 1 name
        1.3. subsection 3 name
        2. Section 2 name
        3. Section 3 name
        """
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

    def _parse_json_response(self, response_content: str, retry_count: int = 0) -> Dict:
        content = response_content.strip()
        
        if "```json" in content:
            parts = content.split("```json")
            if len(parts) > 1:
                content = parts[1].split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            if retry_count >= 2:
                raise ValueError(f"Failed to parse JSON after {retry_count} retries: {str(e)[:200]}") from e
            
            fixed_content = self._llm_fix_json(content, str(e))
            return self._parse_json_response(fixed_content, retry_count + 1)
    
    def _llm_fix_json(self, broken_json: str, error_message: str) -> str:
        fix_prompt = f"""The following JSON has a syntax error. Fix it and return ONLY the corrected JSON.

ERROR: {error_message}

BROKEN JSON:
{broken_json[:3000]}

COMMON ISSUES TO FIX:
1. Escape backslashes in LaTeX: \\frac, \\sin, \\cos should be \\\\frac, \\\\sin, \\\\cos in JSON strings
2. Escape special characters: newlines should be \\n
3. Close unclosed strings, braces, brackets
4. Remove trailing commas before closing braces

Return ONLY the fixed valid JSON, no explanations:"""

        response = self.llm.invoke([
            {"role": "user", "content": fix_prompt}
        ])
        
        return response.content.strip()
