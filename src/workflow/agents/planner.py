from src.utils.llm import chat
from typing import Dict, Any, List
import re
from src.models.context import DocumentContext

class PlannerAgent:

    def __init__(self, model: str):
        self.model = model

    def create_outline(self, context: DocumentContext, feedback: str=None) -> Dict[str, Any]:
        full_text = context.text_content.markdown
        text_length = len(full_text)
        print('Length of document: ', text_length)
        if text_length < 4000:
            target_main_sections = '2'
            max_total_headings = '6'
        elif text_length < 8000:
            target_main_sections = '2'
            max_total_headings = '8'
        elif text_length < 15000:
            target_main_sections = '3'
            max_total_headings = '10'
        else:
            target_main_sections = '4'
            max_total_headings = '12'
        print('target_main_sections', target_main_sections, 'max_total_headings', max_total_headings)
        tables_assets_info = f'# Avaliable Table \n {context.tables}\n # Avaliable Image \n {context.assets.images}'
        feedback_block = ''
        if feedback:
            feedback_block = f'\nREVISION FEEDBACK FROM PREVIOUS OUTLINE REVIEW:\n{feedback}\n\nApply all the suggestions above when generating this revised outline.\n'
        prompt = (
            "# ROLE\n"
            "You are a senior lecture designer and slide-structure architect.\n\n"
            "# TASK\n"
            "Analyze the document and produce a lecture OUTLINE that will be converted into presentation slides.\n\n"
            "HARD CONSTRAINTS (MUST FOLLOW EXACTLY):\n"
            f"- EXACTLY {target_main_sections} lines starting with \"# \"\n"
            f"- Total number of headings (\"# \" + \"## \") MUST be ≤ {max_total_headings}\n"
            "- If a section has subsections, it must have AT LEAST 2 (never exactly 1)\n"
            "- If exceeding limits, you MUST merge sections until valid\n\n"
            "PROPORTIONALITY RULE:\n"
            f"- The source document is {text_length} characters long.\n"
            "- A SHORT document (< 5000 chars / ~2 pages) should produce 4-6 total slides MAX.\n"
            "- A MEDIUM document (5000-15000 chars) should produce 6-10 slides.\n"
            "- A LONG document (> 15000 chars) should produce 8-12 slides.\n"
            "- NEVER inflate a short document into many slides. Consolidate related ideas.\n\n"
            f"FULL DOCUMENT TEXT:\n{full_text}\n"
            f"AVAILABLE TABLES AND IMAGES:\n{tables_assets_info}\n"
            f"{feedback_block}\n\n"
            "# RULES\n"
            "- Same language as the document\n"
            "- Title of each heading: maximum 7 words\n"
            "- 2 heading levels allowed: \"# \" and \"## \"\n"
            "- Do NOT add content absent from the source document\n"
            "- Do NOT include the lecture topic name as a heading\n"
            "- NEVER split one topic into \"Part 1\" and \"Part 2\". If content is related, keep it in ONE heading.\n"
            "- CRITICAL FOR STEM/MATH DOCUMENTS: Worked examples, case studies, numerical problems with specific data "
            "(tables, constraints, solutions) are the MOST IMPORTANT parts. They MUST have their own dedicated section(s).\n"
            "- CRITICAL FOR ALL DOCUMENTS: If the source names specific tools, software, brands, or real-world examples, "
            "these MUST appear in the outline. Never generalize away concrete details.\n"
            "- Return ONLY the markdown outline, no commentary, no explanations\n\n"
            "# EXAMPLE OUTPUT (for illustration only structure, not content):\n\n"
            "# Section One\n"
            "## Subsection A\n"
            "## Subsection B\n"
            "# Section Two\n"
            "# Section Three\n"
            "## Subsection X\n"
            "## Subsection Y\n\n"
        )
        MAX_RETRIES = 3
        target_sections_int = int(target_main_sections)
        max_headings_int = int(max_total_headings)
        for attempt in range(1, MAX_RETRIES + 1):
            outline_md = chat(self.model, [{'role': 'user', 'content': prompt}], temperature=0)
            print(outline_md)
            major_sections = [l for l in outline_md.splitlines() if re.match('^#\\s+\\S', l)]
            all_headings = [l for l in outline_md.splitlines() if re.match('^#{1,2}\\s+\\S', l)]
            n_major = len(major_sections)
            n_total = len(all_headings)
            errors: list[str] = []
            if n_major <= 1:
                errors.append(f"The outline has only {n_major} major section (line starting with '# '). There must be at least 2 major sections.")
            if n_major > target_sections_int:
                errors.append(f'The outline has {n_major} major sections but the target is exactly {target_main_sections}. Merge sections until valid.')
            if n_total > max_headings_int:
                errors.append(f'Total heading count ({n_total}) exceeds {max_total_headings}. Merge or remove subsections.')
            for line in outline_md.splitlines():
                if re.search(r'part\s*[12]', line, re.IGNORECASE):
                    errors.append(f"Heading '{line.strip()}' uses 'Part 1/Part 2' splitting. Merge into a single heading.")
            lines = outline_md.splitlines()
            for (i, line) in enumerate(lines):
                if re.match('^#\\s+\\S', line):
                    sub_count = 0
                    for j in range(i + 1, len(lines)):
                        if re.match('^#\\s+\\S', lines[j]):
                            break
                        if re.match('^##\\s+\\S', lines[j]):
                            sub_count += 1
                    if sub_count == 1:
                        errors.append(f"Major section '{line.strip()}' has exactly 1 subtitle. Each major section must have 0 or at least 2 subtitles — never exactly 1.")
            if not errors:
                print('OUTLINE is VALID')
                break
            else:
                print('OUTLINE is INVALID')
                error_list = '\n'.join((f'- {e}' for e in errors))
                prompt += f"\nOld outline:\n{outline_md}\nYour previous outline FAILED validation with the following errors:\n{error_list}\nLet's think step-by-step and fix ALL errors above. This is non-negotiable.\n"
        return {'outline': outline_md}

    def generate_title(self, outline_md: str) -> str:
        prompt = f'Based on the following lecture outline, generate a concise and descriptive lecture title (max 10 words, no quotes).\n\nOutline:\n{outline_md}\n\nReturn ONLY the title, nothing else.'
        return chat(self.model, [{'role': 'user', 'content': prompt}], temperature=0.3).strip().strip('"').strip("'")