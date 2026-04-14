from src.utils.llm import chat
from typing import Dict, Any, List
import re
from src.models.context import DocumentContext


class PlannerAgent:
    def __init__(self, model: str):
        self.model = model

    def create_outline(self, context: DocumentContext, feedback: str = None) -> Dict[str, Any]:
        full_text = context.text_content.markdown
        text_length = len(full_text)

        print("Length of document: ", text_length)

        if text_length < 6000:
            target_main_sections = "2"
        elif text_length < 12000:
            target_main_sections = "3"
        else:
            target_main_sections = "4"
        print("target_main_sections", target_main_sections)
        tables_assets_info = f"# Avaliable Table \n {context.tables}\n # Avaliable Image \n {context.assets.images}"

        feedback_block = ""
        if feedback:
            feedback_block = f"""
REVISION FEEDBACK FROM PREVIOUS OUTLINE REVIEW:
{feedback}

Apply all the suggestions above when generating this revised outline.
"""

        prompt = f"""
# ROLE
You are a senior lecture designer and slide-structure architect.

# TASK
Analyze the document and produce a lecture OUTLINE that will be converted into presentation slides.
HARD CONSTRAINTS (MUST FOLLOW EXACTLY):
- EXACTLY {target_main_sections} lines starting with "# "
- Total number of headings ("# " + "## ") MUST be ≤ 12
- If a section has subsections, it must have AT LEAST 2 (never exactly 1)
- If exceeding limits, you MUST merge sections until valid

FULL DOCUMENT TEXT:
{full_text}
AVAILABLE TABLES AND IMAGES:
{tables_assets_info}

{feedback_block}

# RULES
- Same language as the document
- Title of each heading: maximum 7 words
- 2 heading levels allowed: "# " and "## " is must be popular.
- Do NOT add content absent from the source document
- Do NOT include the lecture topic name as a heading
- Return ONLY the markdown outline, no commentary, no explanations

# EXAMPLE OUTPUT (for illustration only structure, not content):

# Section One
## Subsection A
## Subsection B
# Section Two
# Section Three
## Subsection X
## Subsection Y

"""

        MAX_RETRIES = 4
        target_sections_int = int(target_main_sections)

        for attempt in range(1, MAX_RETRIES + 1):
            outline_md = chat(self.model, [{"role": "user", "content": prompt}], temperature=0)
            print(outline_md)
            major_sections = [l for l in outline_md.splitlines() if re.match(r"^#\s+\S", l)]
            all_headings = [l for l in outline_md.splitlines() if re.match(r"^#{1,2}\s+\S", l)]
            n_major = len(major_sections)
            n_total = len(all_headings)
            ok_major = (n_major <= target_sections_int)
            ok_total = (n_total <= 12)
            if ok_major and ok_total:
                print("OUTLINE is VALID")
                break
            else:
                print("OUTLINE is INVALID")
                prompt += f"""
Old outline:
{outline_md}
Your previous outline FAILED validation:
A major section is any line that starts with "# " (single hash + space). Let's think step-by-step and 
produce EXACTLY {target_main_sections} and total heading count is less than or equal to 12. This is non-negotiable.
"""

        return {"outline": outline_md}

    def generate_title(self, outline_md: str) -> str:
        """Generate a lecture title based on the outline."""
        prompt = (
            f"Based on the following lecture outline, generate a concise and descriptive lecture title (max 10 words, no quotes).\n\n"
            f"Outline:\n{outline_md}\n\n"
            f"Return ONLY the title, nothing else."
        )
        return chat(self.model, [{"role": "user", "content": prompt}], temperature=0.3).strip().strip('"').strip("'")
