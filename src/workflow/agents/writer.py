from src.utils.llm import chat
from typing import Dict, Optional, List
import json
from src.utils.parse_llm_response import parse_json_response
from dataclasses import asdict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide


class WriterAgent:
    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list, temperature: float = 0.4, max_tokens: int = None) -> str:
        return chat(self.model, messages, temperature=temperature, max_tokens=max_tokens)

    def _extract_relevant_text(self, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        return full_text if len(full_text) <= 15000 else full_text[:15000]

    def _build_batch_system_prompt(self) -> str:
        return """\
# ROLE
You are an expert lecture slide writer specializing in engaging,
pedagogically clear slides derived from structured academic material.

# TASK
You will receive a list of slide specifications and the full source material.
Generate content for ALL slides at once in a single response.

# CORE PRINCIPLE
All generated content must satisfy three quality criteria:
- Faithfulness: Each slide must accurately reflect the meaning, tone, and technical
  content of the source material - do not paraphrase into generic textbook language.
- Coverage: Together, all slides should cover the key ideas, arguments, and details
  present in the source material. No important concept should be omitted.
- Coherence: The slides must be internally consistent and logically connected from
  beginning to end - terminology, notation, and narrative flow must remain uniform
  across the entire deck.

# SLIDE HIERARCHY
The slide titles follow a numbered outline structure. Use the title prefix to
determine the role of each slide and write content accordingly:
- Major slide, that has title matches `N.` (e.g. "1. Introduction", "3. Results"):
  Write a high-level overview. Introduce the theme, state the key questions
  or objectives, and briefly preview what the sub-slides will elaborate on.
  Do NOT go into granular detail - save that for the sub-slides.
- Sub-slide, that has title matches `N.M` or `N.M.K` (e.g. "1.1 Background",
  "2.3 Experimental Setup"):
  Write specific, detailed content that expands on exactly one aspect of
  its parent major slide. Assume the audience already saw the parent overview.

# SLIDE CONSTRUCTION RULES
- Follow the language, tone, and style of the source material.
- Stay strictly within the scope of each slide's description / goal.
- Write 3 to 6 bullet points per slide, each 5–20 words.
- Preserve vivid phrasing, examples, or questions when possible.
- Use proper LaTeX for any mathematical expression.

# MATHEMATICS & NOTATION
- Inline mathematical expressions are wrapped in LaTeX delimiters by using $...$
- Correct LaTeX commands are used consistently:
  - Trigonometric functions: $\\sin$, $\\cos$, $\\tan$
  - Greek letters: $\\alpha$, $\\beta$, $\\pi$
  - Fractions: $\\frac{a}{b}$
  - Superscripts: $x^2$, $\\sin^2 x$
  - Subscripts: $x_1$, $a_n$
  - Symbols: $\\neq$, $\\leq$, $\\geq$, $\\pm$, $\\infty$
- Plain-text mathematical notation is never used.

# CONTENT FORMAT FOR SLIDE TYPE
- For "content" / "have_table" / "have_formula":
    "content": ["Point 1", "Point 2", "Point 3", ...]
- For "two_sub_contents":
    "content": {"Sub Title 1": ["Point 1", "Point 2", ...], "Sub Title 2": ["Point 1", "Point 2", ...]}
- For "comparison":
    "content": "A markdown table summarising the two comparable entities."

# OUTPUT FORMAT
Return ONLY valid JSON — an array with one object per slide, in the same
order as the input specifications:
[
  {
    "slide_number": 1,
    "content": ["Point 1 supporting the slide title", "Point 2 supporting the slide title", "Point 3 supporting the slide title", "Point 4 (optional)", "Point 5 (optional)"]
  },
  {
    "slide_number": 2,
    "content": ["Point 1 supporting the slide title", "Point 2 supporting the slide title", "Point 3 supporting the slide title", "Point 4 (optional)", "Point 5 (optional)"]
  }
]
"""

    def draft_slides(
        self,
        slide_specs: List[Slide],
        context: DocumentContext,
    ) -> List[SlideContent]:
        """
        Primary path: generate content for ALL slides in one LLM call.

        Parameters
        ----------
        slide_specs : list of Slide specs produced by PlanSpecerAgent.
        context     : DocumentContext carrying the source material.

        Returns
        -------
        List[SlideContent] in the same order as slide_specs.
        """
        text_excerpt = self._extract_relevant_text(context)

        specs_payload = []
        for i, spec in enumerate(slide_specs, 1):
            d = asdict(spec)
            if hasattr(d.get("slide_type"), "value"):
                d["slide_type"] = d["slide_type"].value
            else:
                d["slide_type"] = str(d.get("slide_type", ""))
            d["slide_number"] = i
            specs_payload.append(d)

        user_prompt = (
            f"SOURCE MATERIAL:\n{text_excerpt}\n\n"
            f"SLIDE SPECIFICATIONS:\n{json.dumps(specs_payload, ensure_ascii=False, indent=2)}"
        )

        raw = self._chat(
            [
                {"role": "system", "content": self._build_batch_system_prompt()},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=16000,
        )

        return self._parse_batch_response(raw, slide_specs)

    def draft_slides_with_feedback(
        self,
        slide_specs_with_feedback: List[tuple],
        context: DocumentContext,
    ) -> List[SlideContent]:
        """
        Batch-refine path for WriterRefinerAgent.

        Parameters
        ----------
        slide_specs_with_feedback : list of (original_index, Slide, feedback_str) tuples.
            `original_index` is the 1-based position of the slide in the full deck.
        context : DocumentContext carrying the source material.

        Returns
        -------
        List[SlideContent] in the same order as slide_specs_with_feedback.
        """
        text_excerpt = self._extract_relevant_text(context)

        specs_payload = []
        slide_specs_ordered: List[Slide] = []
        for seq_num, (orig_idx, spec, feedback) in enumerate(slide_specs_with_feedback, 1):
            d = asdict(spec)
            if hasattr(d.get("slide_type"), "value"):
                d["slide_type"] = d["slide_type"].value
            else:
                d["slide_type"] = str(d.get("slide_type", ""))
            d["slide_number"] = seq_num
            if feedback:
                d["rewrite_feedback"] = feedback
            specs_payload.append(d)
            slide_specs_ordered.append(spec)

        user_prompt = (
            f"SOURCE MATERIAL:\n{text_excerpt}\n\n"
            f"SLIDE SPECIFICATIONS (with optional rewrite_feedback per slide):\n"
            f"{json.dumps(specs_payload, ensure_ascii=False, indent=2)}"
        )

        raw = self._chat(
            [
                {"role": "system", "content": self._build_batch_system_prompt()},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=16000,
        )

        return self._parse_batch_response(raw, slide_specs_ordered)

    def _parse_batch_response(
        self,
        raw: str,
        slide_specs: List[Slide],
    ) -> List[SlideContent]:
        """Parse the batch JSON array and map each entry back to its Slide spec."""
        invoke_fn = lambda msgs: type("R", (), {"content": self._chat(msgs)})()
        data = parse_json_response(raw, invoke_fn, expect_list=True)

        by_number: Dict[int, object] = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    num = item.get("slide_number")
                    if num is not None:
                        by_number[int(num)] = item.get("content", [])

        results: List[SlideContent] = []
        for i, spec in enumerate(slide_specs, 1):
            content = by_number.get(i, [])
            results.append(SlideContent(slide=spec, content=content))
        return results