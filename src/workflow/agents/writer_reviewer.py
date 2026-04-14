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

        faith_reviews   = await self._evaluate_faithfulness(slides, context)
        cov_reviews     = await self._evaluate_coverage_and_clarity(slides, lecture_plan, context)
        pres_reviews    = await self._evaluate_presentation_quality(slides, lecture_plan)

        merged: Dict[int, SlideReview] = {}
        for idx, slide in enumerate(slides, 1):
            merged[idx] = SlideReview(
                slide_index=idx,
                slide_title=slide.slide.slide_title,
                criteria={},
            )

        for criterion_name, reviews in [
            ("faithfulness",          faith_reviews),
            ("coverage_and_clarity",  cov_reviews),
            ("presentation_quality",  pres_reviews),
        ]:
            for sr in reviews:
                if sr.slide_index in merged:
                    merged[sr.slide_index].criteria[criterion_name] = sr.criteria.get(criterion_name, CriterionResult(criterion=criterion_name))

            for slide_idx in merged:
                if criterion_name not in merged[slide_idx].criteria:
                    merged[slide_idx].criteria[criterion_name] = CriterionResult(criterion=criterion_name, issues=[])

        return WriterReview(slide_reviews=list(merged.values()))

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
Use severity as follows:
- "critical": factual errors, hallucinations, years/numbers changed — set confidence > 0.90 only if you are near-certain
- "major": important phrasing issue, significant omission of a supporting fact — set confidence > 0.85 only if clearly evident
- "minor": style, tone, or phrasing suggestion — set confidence > 0.80 only if genuinely useful
If you are not confident enough to meet the bar for a severity level, omit the issue entirely."""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("faithfulness", content, slides)

    async def _evaluate_coverage_and_clarity(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
        context: DocumentContext,
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are a curriculum reviewer and a student evaluator. Assess both content completeness and conceptual clarity of the slides.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SOURCE DOCUMENT (first 6000 chars):
{context.text_content.markdown[:6000]}

SLIDES:
{slides_json}

Evaluate per slide on TWO dimensions:

COVERAGE (outline completeness):
1. Are sections from the outline missing or too superficial?
2. Does any slide deviate from its intended focus in the outline?
3. Is depth proportional to topic importance?

CLARITY (student comprehension):
1. Are key concepts named and explained without assuming prior knowledge?
2. Is there enough context for a reader with no prior exposure to follow the main idea?
3. Are any undefined terms or jargon used without explanation?

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
        }},
        {{
          "severity": "minor",
          "location": "Slide 5, bullet 3",
          "description": "Term 'backpropagation' used without explanation",
          "suggestion": "Add a one-line definition of backpropagation",
          "confidence_score": 0.75
        }}
      ]
    }}
  ]
}}
Use severity as follows:
- "critical": section from outline entirely missing, or slide content contradicts the planned focus — confidence > 0.90
- "major": coverage is significantly too shallow, or a key concept is unexplained — confidence > 0.85
- "minor": minor terminology gap or a suggestion to add a clarifying sentence — confidence > 0.80
Omit any issue where you are not confident enough to meet the threshold for its severity."""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("coverage_and_clarity", content, slides)


    # ── Criterion 3: Presentation Quality ─────────────────────────────────────
    async def _evaluate_presentation_quality(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )
        prompt = f"""You are an academic examiner evaluating the presentation format and quality of lecture slides.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{slides_json}

Evaluate per slide on TWO dimensions:

FORMAT & PEDAGOGY:
1. Content density: max 5 bullets, each bullet <= 15 words, total <= 75 words per slide?
2. Tone: friendly, conversational, not overly academic?
3. Structure: 3-5 bullets per slide (4-5 ideal)?
4. Flow: logical progression between adjacent slides?

PRESENTATION PROFESSIONALISM:
1. Clear, informative titles (not vague like "More Details")?
2. Consistent terminology used throughout the deck?
3. Balanced and well-organized content?
4. Would an academic examiner approve the overall quality?

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
        }},
        {{
          "severity": "minor",
          "location": "Slide 2 title",
          "description": "Title is vague ('Overview') — should be specific",
          "suggestion": "Rename to reflect the actual topic covered",
          "confidence_score": 0.8
        }}
      ]
    }}
  ]
}}
Use severity as follows:
- "critical": slide has > 5 bullets or > 75 words — hard structural violation — confidence > 0.90
- "major": logical flow broken between adjacent slides, or title is genuinely uninformative — confidence > 0.85
- "minor": tone slightly too formal, or a single bullet could be shorter — confidence > 0.80
Omit any issue where you are not confident enough to meet the threshold for its severity."""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("presentation_quality", content, slides)

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
