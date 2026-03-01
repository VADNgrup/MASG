import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
import re
from src.models.context import DocumentContext
from src.models.slide import CriterionScore, ReviewerFeedback
from src.utils.config import config


class PlannerReviewerAgent:
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model

    async def evaluate(
        self,
        lecture_plan: Dict[str, Any],
        context: DocumentContext,
    ) -> ReviewerFeedback:
        outline_md = lecture_plan.get("outline", "")

        faithfulness  = await self._evaluate_faithfulness(outline_md, context)
        coverage      = await self._evaluate_coverage(outline_md, context)
        structure     = await self._evaluate_structural_logic(outline_md)
        granularity   = await self._evaluate_granularity(outline_md)
        alignment     = await self._evaluate_objective_alignment(outline_md, context)

        # Equal weight: 20% each
        overall_score = (
            faithfulness.score * 0.2 +
            coverage.score     * 0.2 +
            structure.score    * 0.2 +
            granularity.score  * 0.2 +
            alignment.score    * 0.2
        )

        if overall_score >= 80:
            decision = "ACCEPT"
        elif overall_score >= 50:
            decision = "RETRY"
        else:
            decision = "REJECT"

        specific_feedback = self._compile_specific_feedback(
            faithfulness, coverage, structure, granularity, alignment
        )

        return ReviewerFeedback(
            overall_score=overall_score,
            decision=decision,
            criteria={
                "faithfulness":       faithfulness,
                "coverage":           coverage,
                "structural_logic":   structure,
                "granularity":        granularity,
                "objective_alignment": alignment,
            },
            specific_feedback=specific_feedback,
            summary=self._generate_summary(overall_score, decision, specific_feedback),
        )

    # ------------------------------------------------------------------
    # Criterion 1 – Faithfulness to Source
    # ------------------------------------------------------------------
    async def _evaluate_faithfulness(
        self,
        outline_md: str,
        context: DocumentContext,
    ) -> CriterionScore:
        prompt = f"""You are a strict fact-checker reviewing a lecture outline against its source document.

SOURCE DOCUMENT (first 10 000 chars):
{context.text_content.markdown[:10000]}

PROPOSED OUTLINE:
{outline_md}

Evaluate every heading in the outline:
1. Does each heading/section appear to have clear evidence in the source document?
2. Are there any headings that are speculative, inferred, or invented beyond the source?
3. Are any concepts renamed or relabelled in a way that distorts the original meaning?
4. Does any section heading imply content that the source does not actually contain?

Score from 0 to 100 (100 = every heading is traceable to the source).

Return ONLY valid JSON:
{{
  "score": 85,
  "issues": ["Section 'Advanced Optimization' has no evidence in source document", "Heading 'Future Trends' is speculative — not in source"],
  "suggestions": ["Remove or rename 'Advanced Optimization' to match source language", "Replace 'Future Trends' with a section grounded in source content"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 2 – Coverage
    # ------------------------------------------------------------------
    async def _evaluate_coverage(
        self,
        outline_md: str,
        context: DocumentContext,
    ) -> CriterionScore:
        prompt = f"""You are a curriculum designer checking whether a lecture outline adequately covers the source material.

SOURCE DOCUMENT (first 10 000 chars):
{context.text_content.markdown[:10000]}

PROPOSED OUTLINE:
{outline_md}

Evaluate:
1. Are there major themes or topics in the source that are completely missing from the outline?
2. Are any important sections merged together in a way that causes a loss of focus?
3. Is the depth of each section proportional to its prominence in the source?
4. Would a student reading only these slides miss any critical concept from the source?

Score from 0 to 100 (100 = all important themes are covered with appropriate depth).

Return ONLY valid JSON:
{{
  "score": 78,
  "issues": ["Source chapter on 'Error Handling' is entirely absent from the outline", "Sections 2 and 3 are merged, losing the distinction between theory and practice"],
  "suggestions": ["Add a dedicated section for 'Error Handling'", "Split merged section into two separate sections to preserve focus"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 3 – Structural Logic
    # ------------------------------------------------------------------
    async def _evaluate_structural_logic(
        self,
        outline_md: str,
    ) -> CriterionScore:
        prompt = f"""You are a presentation architect reviewing the logical structure of a lecture outline.

PROPOSED OUTLINE:
{outline_md}

Evaluate:
1. Does the outline follow a natural progression (e.g. intro → core concepts → conclusion)?
2. Are there any abrupt topic jumps that break the narrative flow?
3. Are there duplicate or near-duplicate sections?
4. Are any sections too generic or vague to carry meaningful meaning (e.g. 'Overview', 'Misc')?
5. Is the hierarchy (# and ##) used consistently and logically?

Score from 0 to 100 (100 = clean, logical, well-sequenced structure with no redundancy).

Return ONLY valid JSON:
{{
  "score": 80,
  "issues": ["Section 4 'Introduction to Basics' appears after advanced sections — order is illogical", "Sections 2 and 5 cover the same topic"],
  "suggestions": ["Move 'Introduction to Basics' to be the first section", "Merge or differentiate Sections 2 and 5 to remove duplication"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 4 – Granularity
    # ------------------------------------------------------------------
    async def _evaluate_granularity(
        self,
        outline_md: str,
    ) -> CriterionScore:
        prompt = f"""You are a slide-writing coach reviewing whether a lecture outline gives the writer the right level of detail.

PROPOSED OUTLINE:
{outline_md}

Evaluate:
1. Are any major sections too high-level or vague for a writer to know what content to include?
2. Are any sections over-specified to the point where they constrain the writer unnecessarily?
3. Do subsections provide meaningful guidance without becoming prose themselves?
4. Is the granularity consistent across comparable sections?

Score from 0 to 100 (100 = every section gives writers exactly the right level of direction).

Return ONLY valid JSON:
{{
  "score": 72,
  "issues": ["Section 1 'Background' has no subsections and is too vague for a writer to work with", "Section 3 subsections list individual sentences rather than high-level topics — over-specified"],
  "suggestions": ["Break 'Background' into 2-3 focused subsections (e.g. historical context, key definitions)", "Rewrite Section 3 subsections as topic labels, not full sentences"]
}}"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)

    # ------------------------------------------------------------------
    # Criterion 5 – Objective Alignment
    # ------------------------------------------------------------------
    async def _evaluate_objective_alignment(
        self,
        outline_md: str,
        context: DocumentContext,
    ) -> CriterionScore:
        prompt = f"""You are an instructional designer evaluating whether a lecture outline serves its intended purpose as a slide presentation for students.

SOURCE DOCUMENT SUMMARY (first 3 000 chars):
{context.text_content.markdown[:3000]}

PROPOSED OUTLINE:
{outline_md}

The objective is: create slides suitable for a lecture presentation to students.

Evaluate:
1. Is the outline structured for slide-by-slide presentation (not a continuous essay)?
2. Does it have a clear opening section to introduce the topic to an audience?
3. Does it have a logical closing section (summary, conclusion, or takeaways)?
4. Is the scope of each section appropriate for 1–3 slides without requiring excessive compression?
5. Does the outline feel teachable — would an instructor be comfortable delivering this as a lecture?

Score from 0 to 100 (100 = perfectly aligned with lecture slide presentation goals).

Return ONLY valid JSON:
{{
  "score": 76,
  "issues": ["No introductory section to frame the topic for the audience", "Section 5 is too broad to fit on 1-3 slides without massive compression"],
  "suggestions": ["Add an 'Introduction / Motivation' section as the first item", "Split Section 5 into two focused subsections to make it slide-friendly"]
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

        if isinstance(data.get("issues"), list):
            data["issues"] = [
                f"{item['section']}: {item['issue']}" if isinstance(item, dict) and "section" in item and "issue" in item
                else str(item)
                for item in data["issues"]
            ]

        if isinstance(data.get("suggestions"), list):
            data["suggestions"] = [
                f"{item['section']}: {item['suggestion']}" if isinstance(item, dict) and "section" in item and "suggestion" in item
                else str(item)
                for item in data["suggestions"]
            ]

        return CriterionScore(**data)

    def _compile_specific_feedback(
        self,
        faithfulness: CriterionScore,
        coverage: CriterionScore,
        structure: CriterionScore,
        granularity: CriterionScore,
        alignment: CriterionScore,
    ) -> List[Dict[str, str]]:
        feedback = []

        criterion_map = {
            "faithfulness":        faithfulness.issues,
            "coverage":            coverage.issues,
            "structural_logic":    structure.issues,
            "granularity":         granularity.issues,
            "objective_alignment": alignment.issues,
        }

        for criterion_name, issues in criterion_map.items():
            for issue in issues:
                # Try to detect a section reference like "Section 2" or "Section 'Background'"
                match = re.search(r"[Ss]ection[s]?\s+['\"]?([^'\",:]+)['\"]?", issue)
                section_ref = match.group(1).strip() if match else "general"
                feedback.append({
                    "section":   section_ref,
                    "issue":     issue,
                    "criterion": criterion_name,
                })

        return feedback

    def _generate_summary(self, score: float, decision: str, feedback: List[Dict]) -> str:
        if decision == "ACCEPT":
            return f"Outline passed review with score {score:.1f}/100. Ready for writing."
        elif decision == "RETRY":
            return f"Score {score:.1f}/100. Found {len(feedback)} issues — outline needs revision before writing."
        else:
            return f"Score {score:.1f}/100. Outline has major structural/faithfulness issues. Recommend regeneration."
