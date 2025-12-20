from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
import re
from src.models.context import DocumentContext
from src.models.slide import SlideContent, ReviewerFeedback, CriterionScore
from src.utils.config import config
from src.optimization.lightning_integration import lightning_integration

class ReviewerAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model
    
    async def evaluate(
        self, 
        slides: List[SlideContent], 
        context: DocumentContext,
        lecture_plan: Dict[str, Any]
    ) -> ReviewerFeedback:
        faithfulness = await self._evaluate_faithfulness(slides, context)
        pedagogical = await self._evaluate_pedagogical_flow(slides, lecture_plan)
        visual = await self._evaluate_visual_alignment(slides, context)
        
        overall_score = (
            faithfulness.score * 0.4 +
            pedagogical.score * 0.35 +
            visual.score * 0.25
        )
        
        if overall_score >= 75:
            decision = "ACCEPT"
        elif overall_score >= 50:
            decision = "RETRY"
        else:
            decision = "REJECT"
        
        specific_feedback = self._compile_specific_feedback(
            slides, faithfulness, pedagogical, visual
        )
        
        return ReviewerFeedback(
            overall_score=overall_score,
            decision=decision,
            criteria={
                "faithfulness": faithfulness,
                "pedagogical_flow": pedagogical,
                "visual_alignment": visual
            },
            specific_feedback=specific_feedback,
            summary=self._generate_summary(overall_score, decision, specific_feedback)
        )
    
    async def _evaluate_faithfulness(
        self, 
        slides: List[SlideContent], 
        context: DocumentContext
    ) -> CriterionScore:
        prompt = f"""Compare slides against source document. Detect hallucinations.

SOURCE DOCUMENT:
{context.text_content.markdown[:4000]}

SLIDES:
{json.dumps([{"title": s.title, "content": s.content} for s in slides], indent=2)}

Evaluate:
1. Are there any facts/numbers/claims NOT in source?
2. Are there misrepresentations?
3. Are dates, names, statistics accurate?

Return ONLY valid JSON:
{{
  "score": 85,
  "issues": ["Slide 3: Year 2023 changed to 2024"],
  "suggestions": ["Verify dates against source"]
}}"""
        
        lightning_integration.emit_prompt(prompt=prompt, model=self.model, metadata={"agent": "reviewer", "criterion": "faithfulness"})
        
        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)
    
    async def _evaluate_pedagogical_flow(
        self, 
        slides: List[SlideContent],
        lecture_plan: Dict[str, Any]
    ) -> CriterionScore:
        prompt = f"""Evaluate pedagogical quality of slides:

PLANNED OUTLINE:
{json.dumps(lecture_plan, indent=2)}

SLIDES:
{json.dumps([{"title": s.title, "content": s.content} for s in slides], indent=2)}

Check:
1. Text density: Each bullet <= 15 words? Total per slide <= 80 words?
2. Structure: 3-5 bullets per slide?
3. Flow: Logical progression?
4. Clarity: Jargon explained?

Return ONLY valid JSON:
{{
  "score": 75,
  "issues": ["Slide 2 has 6 bullets, too many"],
  "suggestions": ["Reduce to 4-5 key points"]
}}"""
        
        lightning_integration.emit_prompt(prompt=prompt, model=self.model, metadata={"agent": "reviewer", "criterion": "pedagogical_flow"})
        
        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)
    
    async def _evaluate_visual_alignment(
        self,
        slides: List[SlideContent],
        context: DocumentContext
    ) -> CriterionScore:
        slides_with_images = [s for s in slides if s.image]
        
        if not slides_with_images:
            return CriterionScore(score=100, issues=[], suggestions=[])
        
        prompt = f"""Evaluate visual alignment:

SLIDES WITH IMAGES:
{json.dumps([{"title": s.title, "image_query": s.image_query} for s in slides_with_images], indent=2)}

Check:
1. Does image query match slide content?
2. Are there slides that NEED images but don't have them?

Return ONLY valid JSON:
{{
  "score": 80,
  "issues": [],
  "suggestions": []
}}"""
        
        lightning_integration.emit_prompt(prompt=prompt, model=self.model, metadata={"agent": "reviewer", "criterion": "visual_alignment"})
        
        response = await self.llm.ainvoke(prompt)
        return self._parse_criterion_response(response.content)
    
    def _parse_criterion_response(self, content: str) -> CriterionScore:
        try:
            data = json.loads(content)
        except:
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content.split("```json")[1].split("```")[0]
            elif clean_content.startswith("```"):
                clean_content = clean_content.split("```")[1].split("```")[0]
            data = json.loads(clean_content.strip())
        
        return CriterionScore(**data)
    
    def _compile_specific_feedback(
        self,
        slides: List[SlideContent],
        faithfulness: CriterionScore,
        pedagogical: CriterionScore,
        visual: CriterionScore
    ) -> List[Dict[str, str]]:
        feedback = []
        
        for issue in faithfulness.issues + pedagogical.issues + visual.issues:
            match = re.search(r"[Ss]lide[_\s]?(\d+|[a-z0-9_]+)", issue)
            if match:
                slide_ref = match.group(1)
                feedback.append({
                    "slide_id": f"slide_{slide_ref}",
                    "issue": issue,
                    "criterion": self._categorize_issue(issue)
                })
        
        return feedback
    
    def _categorize_issue(self, issue: str) -> str:
        issue_lower = issue.lower()
        
        if any(kw in issue_lower for kw in ["hallucination", "incorrect", "not in source"]):
            return "faithfulness"
        elif any(kw in issue_lower for kw in ["too much text", "too long", "unclear"]):
            return "pedagogical_flow"
        elif any(kw in issue_lower for kw in ["image", "visual", "missing"]):
            return "visual_alignment"
        else:
            return "general"
    
    def _generate_summary(self, score: float, decision: str, feedback: List[Dict]) -> str:
        if decision == "ACCEPT":
            return f"✅ Slides passed review with score {score:.1f}/100. Ready for rendering."
        elif decision == "RETRY":
            issues_count = len(feedback)
            return f"⚠️ Score {score:.1f}/100. Found {issues_count} issues requiring revision."
        else:
            return f"❌ Score {score:.1f}/100. Major issues detected. Recommend regeneration."

