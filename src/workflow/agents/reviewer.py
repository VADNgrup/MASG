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
        faithfulness = await self._evaluate_faithfulness(slides, context)
        pedagogical = await self._evaluate_pedagogical_flow(slides, lecture_plan)
        
        overall_score = (
            faithfulness.score * 0.5 +
            pedagogical.score * 0.5
        )
        
        if overall_score >= 75:
            decision = "ACCEPT"
        elif overall_score >= 50:
            decision = "RETRY"
        else:
            decision = "REJECT"
        
        specific_feedback = self._compile_specific_feedback(
            slides, faithfulness, pedagogical
        )
        
        return ReviewerFeedback(
            overall_score=overall_score,
            decision=decision,
            criteria={
                "faithfulness": faithfulness,
                "pedagogical_flow": pedagogical
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
{context.text_content.markdown[:10000]}

SLIDES:
{json.dumps([{"slide_title": s.slide_title, "content": s.content} for s in slides], indent=2)}

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
{json.dumps([{"slide_title": s.slide_title, "content": s.content} for s in slides], indent=2)}

Check:
1. Content density: Maximum 5 bullets per slide? Each bullet <= 15 words? Total per slide <= 75 words?
2. Tone: Is the language friendly, approachable, and conversational? Avoid overly formal, rigid, or academic tone.
3. Structure: 3-5 bullets per slide? (4-5 is ideal, 6+ is too many)
4. Flow: Logical progression between slides?
5. Clarity: Easy to understand? Jargon explained in friendly terms?

Return ONLY valid JSON:
{{
  "score": 75,
  "issues": ["Slide 2 has 7 bullets, too dense - should be max 5", "Slide 3 uses overly formal academic language"],
  "suggestions": ["Split into 2 slides or reduce to 4-5 key points", "Use more friendly, conversational tone"]
}}"""
        
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
        
        # Safely handle issues list
        if isinstance(data.get("issues"), list):
            processed_issues = []
            for item in data["issues"]:
                if isinstance(item, dict):
                    # Try to extract issue from dict, fallback to string representation
                    if 'issue' in item and 'slide' in item:
                        processed_issues.append(f"Slide {item['slide']}: {item['issue']}")
                    else:
                        # Just convert entire dict to string if structure is different
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
        pedagogical: CriterionScore
    ) -> List[Dict[str, str]]:
        feedback = []
        
        for issue in faithfulness.issues + pedagogical.issues:
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
        else:
            return "general"
    
    def _generate_summary(self, score: float, decision: str, feedback: List[Dict]) -> str:
        if decision == "ACCEPT":
            return f"Slides passed review with score {score:.1f}/100. Ready for rendering."
        elif decision == "RETRY":
            issues_count = len(feedback)
            return f"Score {score:.1f}/100. Found {issues_count} issues requiring revision."
        else:
            return f"Score {score:.1f}/100. Major issues detected. Recommend regeneration."

