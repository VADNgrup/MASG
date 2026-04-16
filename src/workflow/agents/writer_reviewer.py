import asyncio
from src.utils.llm import chat, achat
from typing import List, Dict, Any
import json
from dataclasses import asdict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.models.feedback import Issue, CriterionResult, SlideReview, WriterReview, Severity


class ReviewerAgent:
    def __init__(self, model: str):
        self.model = model

    async def evaluate(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
        lecture_plan: Dict[str, Any],
        slide_specs: List[Slide] = None,
    ) -> WriterReview:

        faith_reviews, cov_reviews, pres_reviews = await asyncio.gather(
            self._evaluate_faithfulness(slides, context),
            self._evaluate_coverage_and_clarity(slides, lecture_plan, slide_specs or []),
            self._evaluate_presentation_quality(slides, lecture_plan),
        )

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
        slide_specs: List[Slide],
    ) -> List[SlideReview]:
        slides_json = json.dumps(
            [{"slide_number": i, "slide_title": s.slide.slide_title, "content": s.content} for i, s in enumerate(slides, 1)],
            indent=2
        )

        specs_json = json.dumps(
            [
                {
                    "slide_number": i,
                    "slide_title": spec.slide_title,
                    "goal": spec.goal,
                }
                for i, spec in enumerate(slide_specs, 1)
            ],
            indent=2,
            ensure_ascii=False,
        ) if slide_specs else "(no specs provided)"

        prompt = f"""You are a curriculum reviewer. Your primary job is to verify that each slide strictly achieves its stated goal.

SLIDE SPECIFICATIONS (the intended goal each slide MUST fulfil):
{specs_json}

SLIDES (actual generated content to evaluate):
{slides_json}

# CORE RULE
Each slide has an explicit goal defined in the spec above.
A slide PASSES only if its content directly and fully addresses that goal.
A slide FAILS if its content is off-topic, too vague, or covers only a superficial part of the goal.

Evaluate per slide on TWO dimensions:

COVERAGE — Goal adherence (most important):
1. Does EVERY key idea stated in the goal appear in the slide content?
2. Is there any part of the goal that is completely missing from the content?
3. Does the slide drift away from its intended focus and cover something not in the goal?

CLARITY — Student comprehension:
1. Are key concepts named and explained without assuming prior knowledge?
2. Are any undefined terms or jargon used without explanation?

Return ONLY valid JSON listing only slides WITH issues:
{{
  "slide_reviews": [
    {{
      "slide_number": 5,
      "issues": [
        {{
          "severity": "critical",
          "location": "Slide 5",
          "description": "Goal required explaining X method in detail, but slide only names it without any elaboration",
          "suggestion": "Add 2-3 bullets explaining how X method works as specified in the goal",
          "confidence_score": 0.93
        }},
      ]
    }}
  ]
}}
Use severity as follows:
- "critical": slide completely fails its goal, or major part of the goal is absent — confidence > 0.90
- "major": goal only partially met, an important concept from the goal is missing or too shallow — confidence > 0.85
- "minor": minor gap in clarity or a small suggestion to better fulfil the goal — confidence > 0.80
Omit any issue where you are not confident enough to meet the threshold for its severity."""

        content = await achat(self.model, [{"role": "user", "content": prompt}], temperature=0.2)
        return self._parse_slide_reviews("coverage_and_clarity", content, slides)

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
