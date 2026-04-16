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

        MAX_RETRIES = 3
        target_sections_int = int(target_main_sections)

        for attempt in range(1, MAX_RETRIES + 1):
            outline_md = chat(self.model, [{"role": "user", "content": prompt}], temperature=0)
            print(outline_md)
            major_sections = [l for l in outline_md.splitlines() if re.match(r"^#\s+\S", l)]
            all_headings = [l for l in outline_md.splitlines() if re.match(r"^#{1,2}\s+\S", l)]
            n_major = len(major_sections)
            n_total = len(all_headings)

            # --- validation checks ---
            errors: list[str] = []

            # Rule 1: must have more than 1 major section
            if n_major <= 1:
                errors.append(
                    f"The outline has only {n_major} major section (line starting with '# '). "
                    f"There must be at least 2 major sections."
                )

            # Rule 2: total major count must not exceed target
            if n_major > target_sections_int:
                errors.append(
                    f"The outline has {n_major} major sections but the target is "
                    f"exactly {target_main_sections}. Merge sections until valid."
                )
            # Rule 3: total slide count > 15 is invalid (each heading = 1 slide)
            if n_total > 15:
                errors.append(
                    f"Total slide count ({n_total}) exceeds 15. "
                    f"Reduce the number of headings so the deck has at most 15 slides."
                )

            # Rule 5: no major section may have exactly 1 subtitle
            lines = outline_md.splitlines()
            for i, line in enumerate(lines):
                if re.match(r"^#\s+\S", line):
                    # count consecutive ## lines belonging to this major
                    sub_count = 0
                    for j in range(i + 1, len(lines)):
                        if re.match(r"^#\s+\S", lines[j]):
                            break          # reached next major
                        if re.match(r"^##\s+\S", lines[j]):
                            sub_count += 1
                    if sub_count == 1:
                        errors.append(
                            f"Major section '{line.strip()}' has exactly 1 subtitle. "
                            f"Each major section must have 0 or at least 2 subtitles — never exactly 1."
                        )

            if not errors:
                print("OUTLINE is VALID")
                break
            else:
                print("OUTLINE is INVALID")
                error_list = "\n".join(f"- {e}" for e in errors)
                prompt += f"""
Old outline:
{outline_md}
Your previous outline FAILED validation with the following errors:
{error_list}
Let's think step-by-step and fix ALL errors above. This is non-negotiable.
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
