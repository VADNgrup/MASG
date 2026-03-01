import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
import re
from src.models.context import DocumentContext
from src.models.slide import SlideContent, ReviewerFeedback, CriterionScore
from src.utils.config import config

class ReviewerAgent:
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model

    async def evaluate(
        self,
        slides: List[SlideContent],
        context: DocumentContext,
        lecture_plan: Dict[str, Any]
    ) -> ReviewerFeedback:
        faithfulness   = await self._evaluate_faithfulness(slides, context)
        pedagogical    = await self._evaluate_pedagogical_flow(slides, lecture_plan)
        coverage       = await self._evaluate_coverage(slides, lecture_plan, context)
        viewer         = await self._evaluate_viewer(slides, context)
        observer       = await self._evaluate_observer(slides, lecture_plan)

        # Equal weight: 20% each
        overall_score = (
            faithfulness.score * 0.2 +
            pedagogical.score  * 0.2 +
            coverage.score     * 0.2 +
            viewer.score       * 0.2 +
            observer.score     * 0.2
        )

        if overall_score >= 80:
            decision = "ACCEPT"
        elif overall_score >= 50:
            decision = "RETRY"
        else:
            decision = "REJECT"

        specific_feedback = self._compile_specific_feedback(
            slides, faithfulness, pedagogical, coverage, viewer, observer
        )

        return ReviewerFeedback(
            overall_score=overall_score,
            decision=decision,
            criteria={
                "faithfulness":     faithfulness,
                "pedagogical_flow": pedagogical,
                "coverage":         coverage,
                "viewer":           viewer,
                "observer":         observer,
            },
            specific_feedback=specific_feedback,
            summary=self._generate_summary(overall_score, decision, specific_feedback)
        )

    # ------------------------------------------------------------------
    # Criterion 1 – Faithfulness
    # ------------------------------------------------------------------
    async def _evaluate_faithfulness(
        self,
        slides: List[SlideContent],
        context: DocumentContext
    ) -> CriterionScore:
        slides_json = json.dumps(
            [{"slide_title": s.slide_title, "content": s.content} for s in slides],
            indent=2
        )
        prompt = f"""You are a fact-checker. Compare the slides against the source document and detect any inaccuracies or hallucinations.

SOURCE DOCUMENT:
{context.text_content.markdown[:10000]}

SLIDES:
{slides_json}

Evaluate each slide on these points:
1. Is there any information NOT present in the source document?
2. Are there unsupported claims or conclusions?
3. Does any slide over-infer or extrapolate beyond what the source states?
4. Are statistics, names, dates, and technical terms accurate?

Score from 0 to 100 (100 = perfectly faithful). Deduct points for every violation.

Return ONLY valid JSON:
{{
  "score": 85,
  "issues": ["Slide 3: Year 2023 changed to 2024 (source says 2023)", "Slide 5: Claim not supported by source"],
  "suggestions": ["Verify all dates against source", "Remove unsupported inference in Slide 5"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 2 – Pedagogical Flow
    # ------------------------------------------------------------------
    async def _evaluate_pedagogical_flow(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any]
    ) -> CriterionScore:
        slides_json = json.dumps(
            [{"slide_title": s.slide_title, "content": s.content} for s in slides],
            indent=2
        )
        prompt = f"""Evaluate the pedagogical quality of the slides:

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{slides_json}

Check:
1. Content density: Maximum 5 bullets per slide? Each bullet <= 15 words? Total per slide <= 75 words?
2. Tone: Is the language friendly, approachable, and conversational? Avoid overly formal, rigid, or academic tone.
3. Structure: 3-5 bullets per slide? (4-5 is ideal, 6+ is too many)
4. Flow: Logical progression between slides?
5. Clarity: Easy to understand? Jargon explained in friendly terms?

Score from 0 to 100.

Return ONLY valid JSON:
{{
  "score": 75,
  "issues": ["Slide 2 has 7 bullets, too dense - should be max 5", "Slide 3 uses overly formal academic language"],
  "suggestions": ["Split into 2 slides or reduce to 4-5 key points", "Use more friendly, conversational tone"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 3 – Coverage
    # ------------------------------------------------------------------
    async def _evaluate_coverage(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any],
        context: DocumentContext
    ) -> CriterionScore:
        slides_json = json.dumps(
            [{"slide_number": s.slide_number, "slide_title": s.slide_title, "content": s.content} for s in slides],
            indent=2
        )
        prompt = f"""You are a curriculum reviewer. Evaluate how completely the slides cover the intended lecture outline and source material.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SOURCE DOCUMENT SUMMARY (first 5000 chars):
{context.text_content.markdown[:5000]}

SLIDES:
{slides_json}

Evaluate:
1. Are there any sections or topics from the outline that are missing from the slides?
2. Are any sections written too superficially (only 1-2 bullets for a major topic)?
3. Does any section deviate from its intended focus in the outline?
4. Is the depth of each section proportional to its importance in the outline?

Score from 0 to 100 (100 = complete coverage with appropriate depth).

Return ONLY valid JSON:
{{
  "score": 80,
  "issues": ["Section '2.3 Applications' from outline is missing entirely", "Section 1 is too shallow - only 1 bullet for a major topic"],
  "suggestions": ["Add slides for Section 2.3", "Expand Section 1 with at least 3-4 key points"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 4 – Viewer (Self-sufficiency for the audience)
    # ------------------------------------------------------------------
    async def _evaluate_viewer(
        self,
        slides: List[SlideContent],
        context: DocumentContext
    ) -> CriterionScore:
        slides_json = json.dumps(
            [{"slide_number": s.slide_number, "slide_title": s.slide_title, "content": s.content} for s in slides],
            indent=2
        )
        prompt = f"""You are a student who has NOT read the source document. You can only read the slides.

SOURCE DOCUMENT (for reference, do NOT assume the student has read it):
{context.text_content.markdown[:8000]}

SLIDES:
{slides_json}

Evaluate whether a student could understand the lecture topic by reading only the slides:
1. Are key concepts explained or at least named clearly, without assuming prior knowledge?
2. Do the slides provide enough context to follow the main ideas without the source document?
3. Are there slides that reference something without introducing it first?
4. Is the synthesis level appropriate - concise but not cryptic?
5. Would someone reading only the slides walk away with a coherent understanding of the topic?

Score from 0 to 100 (100 = fully self-sufficient; reader can understand without the source).

Return ONLY valid JSON:
{{
  "score": 70,
  "issues": ["Slide 4 uses term 'XYZ' without defining it", "Slide 7 assumes the reader knows the algorithm from Slide 2 but the connection is not stated"],
  "suggestions": ["Add a brief definition of 'XYZ' in Slide 4", "Add a transition sentence in Slide 7 referencing the algorithm"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 5 – Observer (Presentation quality as a lecturer/examiner)
    # ------------------------------------------------------------------
    async def _evaluate_observer(
        self,
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any]
    ) -> CriterionScore:
        slides_json = json.dumps(
            [{"slide_number": s.slide_number, "slide_title": s.slide_title, "content": s.content} for s in slides],
            indent=2
        )
        prompt = f"""You are an academic examiner observing a lecture presentation. Evaluate whether these slides would make for a professional, credible, and engaging lecture.

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{slides_json}

Evaluate:
1. Professional presentation: Are titles clear and informative? Is the overall structure coherent?
2. Engagement: Do the slides guide the audience through a meaningful narrative?
3. Academic credibility: Is the content balanced, well-organized, and appropriately detailed?
4. Consistency: Is terminology used consistently throughout? Is the style uniform?
5. Overall impression: Would an examiner or supervisor approve this as a quality lecture presentation?

Score from 0 to 100 (100 = exemplary lecture presentation that would impress any examiner).

Return ONLY valid JSON:
{{
  "score": 78,
  "issues": ["Slide 6 title is vague ('More Details') - should be specific", "Terminology inconsistency: 'model' and 'algorithm' used interchangeably"],
  "suggestions": ["Rename Slide 6 to reflect its actual topic", "Standardize terminology: choose 'model' or 'algorithm' and use it consistently"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_criterion_response(self, content: str) -> CriterionScore:
        try:
            data = json.loads(content)
        except Exception:
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content.split("```json")[1].split("```")[0]
            elif clean_content.startswith("```"):
                clean_content = clean_content.split("```")[1].split("```")[0]
            data = json.loads(clean_content.strip())

        # Safely handle issues list
        if isinstance(data.get("issues"), list):
            processed_issues = []
            for item in data["issues"]:
                if isinstance(item, dict):
                    if 'issue' in item and 'slide' in item:
                        processed_issues.append(f"Slide {item['slide']}: {item['issue']}")
                    else:
                        processed_issues.append(str(item))
                else:
                    processed_issues.append(str(item))
            data["issues"] = processed_issues

        # Safely handle suggestions list
        if isinstance(data.get("suggestions"), list):
            processed_suggestions = []
            for item in data["suggestions"]:
                if isinstance(item, dict):
                    if 'suggestion' in item and 'slide' in item:
                        processed_suggestions.append(f"Slide {item['slide']}: {item['suggestion']}")
                    else:
                        processed_suggestions.append(str(item))
                else:
                    processed_suggestions.append(str(item))
            data["suggestions"] = processed_suggestions

        return CriterionScore(**data)

    def _compile_specific_feedback(
        self,
        slides: List[SlideContent],
        faithfulness: CriterionScore,
        pedagogical: CriterionScore,
        coverage: CriterionScore,
        viewer: CriterionScore,
        observer: CriterionScore,
    ) -> List[Dict[str, str]]:
        feedback = []

        criterion_map = {
            "faithfulness":     faithfulness.issues,
            "pedagogical_flow": pedagogical.issues,
            "coverage":         coverage.issues,
            "viewer":           viewer.issues,
            "observer":         observer.issues,
        }

        for criterion_name, issues in criterion_map.items():
            for issue in issues:
                match = re.search(r"[Ss]lide[_\s]?(\d+|[a-z0-9_]+)", issue)
                if match:
                    slide_ref = match.group(1)
                    feedback.append({
                        "slide_id":  f"slide_{slide_ref}",
                        "issue":     issue,
                        "criterion": criterion_name,
                    })

        return feedback

    def _generate_summary(self, score: float, decision: str, feedback: List[Dict]) -> str:
        if decision == "ACCEPT":
            return f"Slides passed review with score {score:.1f}/100. Ready for rendering."
        elif decision == "RETRY":
            issues_count = len(feedback)
            return f"Score {score:.1f}/100. Found {issues_count} issues requiring revision."
        else:
            return f"Score {score:.1f}/100. Major issues detected. Recommend regeneration."
