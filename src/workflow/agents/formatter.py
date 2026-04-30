from src.utils.llm import chat
from typing import List, Dict, Any
import json
from src.models.slide import SlideContent, Slide
from src.models.feedback import WriterReview
from src.utils.parse_llm_response import parse_json_response
from dataclasses import asdict

class FormatterAgent:
    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list) -> str:
        return chat(self.model, messages, temperature=0.3, max_tokens=8000)

    def _build_system_prompt(self) -> str:
        return """# ROLE
You are a professional Presentation Formatter who creates slides that follow the "Less is More" principle.

# TASK
You will receive draft paragraphs/content for presentation slides, along with any feedback from a Reviewer (fact-checker).
Your job is to convert the raw text into clean, concise KEYWORD-STYLE bullet points — NOT full sentences.

# RULES
1. ADDRESS REVIEWER FEEDBACK: If the reviewer flagged any factual errors or hallucinations, YOU MUST CORRECT THEM in your final output.
2. KEYWORD BULLETS (CRITICAL):
   - Each bullet should be a SHORT phrase or keyword cluster (5-12 words ideal, 15 words MAX).
   - WRONG: "Electronic Lab Notebooks are digital platforms that replace traditional paper lab notebooks for recording experimental data"
   - RIGHT: "ELN: digital replacement for paper lab notebooks"
   - WRONG: "The simplex method was developed by George Dantzig in 1947 and remains widely used today"
   - RIGHT: "Simplex method — George Dantzig, 1947"
3. BULLET COUNT: 3 to 5 bullets per slide. No more than 5.
4. PRESERVE SPECIFICS: Keep ALL proper nouns, software names, numbers, and concrete examples from the draft.
   - If draft mentions "BIOVIA, labguru, labfolder, RSpace, eLABJOURNAL", ALL must appear in output.
5. HIERARCHY: Use sub-bullets sparingly — only when grouping 2-3 tightly related items under a parent.
6. TONE: Professional, clean, scannable at a glance.
7. MATHEMATICS: Retain all LaTeX formulas ($...$) exactly as written.

# CONTENT FORMAT FOR SLIDE TYPE
- For "content" / "have_table" / "have_formula":
    "content": ["Keyword phrase 1", "Keyword phrase 2", "Keyword phrase 3"]
- For "two_sub_contents":
    "content": {"Sub Title 1": ["Phrase 1", "Phrase 2"], "Sub Title 2": ["Phrase 1", "Phrase 2"]}
- For "comparison":
    "content": "A markdown table summarising the two comparable entities."

# OUTPUT FORMAT
Return ONLY valid JSON matching the array format:
[
  {
    "slide_number": 1,
    "content": ["Keyword phrase 1", "Keyword phrase 2"]
  }
]"""

    def format_slides(self, slides: List[SlideContent], slide_specs: List[Slide], review: WriterReview) -> List[SlideContent]:
        payload = []
        review_dict = {r.slide_index: r for r in review.slide_reviews} if review else {}
        
        for slide in slides:
            idx = slide.slide.slide_number
            sr = review_dict.get(idx)
            feedback_issues = []
            if sr and not sr.passed:
                for issue in sr.convincing_issues:
                    feedback_issues.append(f"[{issue.severity.value}] {issue.description} -> SUGGESTION: {issue.suggestion}")
            
            payload.append({
                "slide_number": idx,
                "slide_title": slide.slide.slide_title,
                "draft_content": slide.content,
                "reviewer_feedback_to_fix": feedback_issues if feedback_issues else "None - Clean"
            })
            
        user_prompt = f"SLIDES TO FORMAT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        
        raw = self._chat([
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_prompt}
        ])
        
        invoke_fn = lambda msgs: type('R', (), {'content': self._chat(msgs)})()
        data = parse_json_response(raw, invoke_fn, expect_list=True)
        
        by_number: Dict[int, Any] = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    num = item.get("slide_number")
                    if num is not None:
                        by_number[int(num)] = item.get("content", [])
                        
        formatted_slides = []
        for slide in slides:
            idx = slide.slide.slide_number
            new_content = by_number.get(idx, slide.content)
            formatted_slides.append(SlideContent(slide=slide.slide, content=new_content))
            
        return formatted_slides
