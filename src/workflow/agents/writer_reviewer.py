from src.utils.llm import chat, achat
from typing import List, Dict, Any
import json
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.models.feedback import Issue, CriterionResult, SlideReview, WriterReview, Severity


class ReviewerAgent:
    def __init__(self, model: str):
        self.model = model

    async def evaluate(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
        lecture_plan: Dict[str, Any],
    ) -> WriterReview:

        faith_reviews  = await self._evaluate_faithfulness(slides, context)
        ped_reviews    = await self._evaluate_pedagogical_flow(slides, lecture_plan)
        cov_reviews    = await self._evaluate_coverage(slides, lecture_plan, context)
        viewer_reviews = await self._evaluate_viewer(slides, context)
        obs_reviews    = await self._evaluate_observer(slides, lecture_plan)

        merged: Dict[int, SlideReview] = {}
        for idx, slide in enumerate(slides, 1):
            merged[idx] = SlideReview(
                slide_index=idx,
                slide_title=slide.slide.slide_title,
                criteria={},
            )

        for criterion_name, reviews in [
            ("faithfulness",     faith_reviews),
            ("pedagogical_flow", ped_reviews),
            ("coverage",         cov_reviews),
            ("viewer",           viewer_reviews),
            ("observer",         obs_reviews),
        ]:
            for sr in reviews:
                if sr.slide_index in merged:
                    merged[sr.slide_index].criteria[criterion_name] = sr.criteria.get(criterion_name, CriterionResult(criterion=criterion_name))

            for slide_idx in merged:
                if criterion_name not in merged[slide_idx].criteria:
                    merged[slide_idx].criteria[criterion_name] = CriterionResult(criterion=criterion_name, issues=[])

        return WriterReview(slide_reviews=list(merged.values()))

    # Faithfulness
    async def _evaluate_faithfulness(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are a fact-checker. Compare the slides against the source document and detect any inaccuracies or hallucinations.

SOURCE DOCUMENT:
{context.text_content.markdown[:10000]}

SLIDES:
{slides_json}

For each slide that has issues, return a JSON entry. Slides with no issues should NOT appear in the list.

Return ONLY valid JSON:
{{
  "slide_reviews": [
    {{
      "slide_number": 3,
      "issues": [
        {{
          "severity": "critical",
          "location": "Slide 3, bullet 2",
          "description": "Year 2023 changed to 2024 — source says 2023",
          "suggestion": "Revert to 2023 as stated in the source",
          "confidence_score": 0.95
        }}
      ]
    }}
  ]
}}
Use severity "critical" for factual errors, "minor" for style/phrasing issues."""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("faithfulness", content, slides)

    # Pedagogical Flow
    async def _evaluate_pedagogical_flow(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""Evaluate the pedagogical quality of the slides.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{slides_json}

Check per slide:
1. Content density: max 5 bullets, each bullet <= 15 words, total <= 75 words per slide?
2. Tone: friendly, conversational, not overly academic?
3. Structure: 3-5 bullets per slide (4-5 ideal)?
4. Flow: logical progression between slides?
5. Clarity: jargon explained?

Return ONLY valid JSON listing only slides WITH issues:
{{
  "slide_reviews": [
    {{
      "slide_number": 2,
      "issues": [
        {{
          "severity": "critical",
          "location": "Slide 2",
          "description": "7 bullets — exceeds maximum of 5",
          "suggestion": "Split into 2 slides or reduce to 4-5 key points",
          "confidence_score": 0.9
        }}
      ]
    }}
  ]
}}"""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("pedagogical_flow", content, slides)

    # Coverage
    async def _evaluate_coverage(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
        context: DocumentContext,
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are a curriculum reviewer. Evaluate how completely the slides cover the intended lecture outline and source material.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SOURCE DOCUMENT SUMMARY (first 5000 chars):
{context.text_content.markdown[:5000]}

SLIDES:
{slides_json}

Evaluate per slide:
1. Are sections from the outline missing or too superficial?
2. Does any slide deviate from its intended focus?
3. Is depth proportional to topic importance?

Return ONLY valid JSON listing only slides WITH issues:
{{
  "slide_reviews": [
    {{
      "slide_number": 5,
      "issues": [
        {{
          "severity": "critical",
          "location": "Slide 5",
          "description": "Section '2.3 Applications' from outline is missing entirely",
          "suggestion": "Add content covering the Applications section",
          "confidence_score": 0.88
        }}
      ]
    }}
  ]
}}"""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("coverage", content, slides)

    # Viewer (Student)
    async def _evaluate_viewer(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are a student who has NOT read the source document. You can only read the slides.

SOURCE DOCUMENT (for reference only):
{context.text_content.markdown[:8000]}

SLIDES:
{slides_json}

Evaluate per slide whether a student could understand the topic by reading only the slides:
1. Key concepts named/explained without assuming prior knowledge?
2. Enough context to follow main ideas?
3. References to undefined terms?
4. Would a slide-only reader walk away with coherent understanding?

Return ONLY valid JSON listing only slides WITH issues:
{{
  "slide_reviews": [
    {{
      "slide_number": 4,
      "issues": [
        {{
          "severity": "minor",
          "location": "Slide 4, bullet 1",
          "description": "Term 'XYZ' used without definition",
          "suggestion": "Add a brief definition of 'XYZ'",
          "confidence_score": 0.7
        }}
      ]
    }}
  ]
}}"""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("viewer", content, slides)

    # Observer (Presentation quality)
    async def _evaluate_observer(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are an academic examiner observing a lecture presentation.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{slides_json}

Evaluate per slide:
1. Professional presentation: clear, informative titles?
2. Engagement: guides audience through meaningful narrative?
3. Academic credibility: balanced, well-organized?
4. Consistency: terminology uniform throughout?
5. Overall impression: would an examiner approve?

Return ONLY valid JSON listing only slides WITH issues:
{{
  "slide_reviews": [
    {{
      "slide_number": 6,
      "issues": [
        {{
          "severity": "minor",
          "location": "Slide 6 title",
          "description": "Title is vague ('More Details') — should be specific",
          "suggestion": "Rename Slide 6 to reflect its actual topic",
          "confidence_score": 0.8
        }}
      ]
    }}
  ]
}}"""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("observer", content, slides)

    def _parse_slide_reviews(
        self,
        criterion_name: str,
        content: str,
        slides: List[SlideContent],
    ) -> List[SlideReview]:
        """Parse LLM response into a list of SlideReview objects for this criterion."""
        try:
            data = json.loads(content)
        except Exception:
            clean = content.strip()
            if clean.startswith("```json"):
                clean = clean.split("```json")[1].split("```")[0]
            elif clean.startswith("```"):
                clean = clean.split("```")[1].split("```")[0]
            try:
                data = json.loads(clean.strip())
            except Exception:
                return []

        valid_indices = set(range(1, len(slides) + 1))
        result: List[SlideReview] = []

        for entry in data.get("slide_reviews", []):
            if not isinstance(entry, dict):
                continue
            slide_number = int(entry.get("slide_number", -1))
            if slide_number not in valid_indices:
                continue

            slide = slides[slide_number - 1]
            issues: List[Issue] = []
            for item in entry.get("issues", []):
                if not isinstance(item, dict):
                    continue
                try:
                    severity = Severity(item.get("severity", "minor").lower())
                except ValueError:
                    severity = Severity.MINOR
                issues.append(Issue(
                    severity=severity,
                    location=str(item.get("location", f"Slide {slide_number}")),
                    description=str(item.get("description", "")),
                    suggestion=str(item.get("suggestion", "")),
                    confidence_score=float(item.get("confidence_score", 0.0)),
                ))

            result.append(SlideReview(
                slide_index=slide_number,
                slide_title=slide.slide.slide_title,
                criteria={criterion_name: CriterionResult(criterion=criterion_name, issues=issues)},
            ))

        return result
