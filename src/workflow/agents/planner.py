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
        if text_length < 6000:
            target_main_sections = '2'
        elif text_length < 12000:
            target_main_sections = '3'
        else:
            target_main_sections = '4'
        print('target_main_sections', target_main_sections)
        tables_assets_info = f'# Avaliable Table \n {context.tables}\n # Avaliable Image \n {context.assets.images}'
        feedback_block = ''
        if feedback:
            feedback_block = f'\nREVISION FEEDBACK FROM PREVIOUS OUTLINE REVIEW:\n{feedback}\n\nApply all the suggestions above when generating this revised outline.\n'
        prompt = f'\n# ROLE\nYou are a senior lecture designer and slide-structure architect.\n\n# TASK\nAnalyze the document and produce a lecture OUTLINE that will be converted into presentation slides.\nHARD CONSTRAINTS (MUST FOLLOW EXACTLY):\n- EXACTLY {target_main_sections} lines starting with "# "\n- Total number of headings ("# " + "## ") MUST be ≤ 12\n- If a section has subsections, it must have AT LEAST 2 (never exactly 1)\n- If exceeding limits, you MUST merge sections until valid\n\nFULL DOCUMENT TEXT:\n{full_text}\nAVAILABLE TABLES AND IMAGES:\n{tables_assets_info}\n\n{feedback_block}\n\n# RULES\n- Same language as the document\n- Title of each heading: maximum 7 words\n- 2 heading levels allowed: "# " and "## " is must be popular.\n- Do NOT add content absent from the source document\n- Do NOT include the lecture topic name as a heading\n- Return ONLY the markdown outline, no commentary, no explanations\n\n# EXAMPLE OUTPUT (for illustration only structure, not content):\n\n# Section One\n## Subsection A\n## Subsection B\n# Section Two\n# Section Three\n## Subsection X\n## Subsection Y\n\n'
        MAX_RETRIES = 3
        target_sections_int = int(target_main_sections)
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
            if n_total > 15:
                errors.append(f'Total slide count ({n_total}) exceeds 15. Reduce the number of headings so the deck has at most 15 slides.')
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