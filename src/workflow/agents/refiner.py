from langchain_openai import ChatOpenAI
from typing import Dict, Optional
import json
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.utils.config import config

class SlideRefinerAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
    
    def refine_slide(
        self,
        original_slide: SlideContent,
        missing_info: list,
        source_text: str,
        language: str
    ) -> SlideContent:
        
        system_prompt = f"""You are refining a lecture slide to add missing information while maintaining a friendly, approachable tone.

The original slide is incomplete. Your task:
1. Keep all existing good content
2. ADD the missing information listed below, prioritizing the most important points
3. Ensure MAXIMUM 5 bullet points total (combine or prioritize if needed)
4. Maintain friendly, conversational tone - warm and approachable, not formal or rigid
5. Expand speaker notes with the missing context (4-6 sentences, conversational)

Write in {language} language with a friendly, engaging tone.

Return ONLY valid JSON with complete slide structure."""

        user_prompt = f"""ORIGINAL SLIDE:
Title: {original_slide.title}
Content: {json.dumps(original_slide.content, ensure_ascii=False)}
Speaker Notes: {original_slide.speaker_notes}

MISSING INFORMATION TO ADD:
{chr(10).join(f"- {info}" for info in missing_info[:5])}

RELEVANT SOURCE TEXT:
{source_text[:3000]}

Generate REFINED slide with:
- Same title
- MAXIMUM 5 bullet points total (combine original and missing info, prioritize the most important)
- Use friendly, conversational language - be warm and approachable
- Speaker notes (4-6 sentences) covering everything in a friendly, conversational way
- Same image_query

IMPORTANT: If adding missing info would exceed 5 bullets, prioritize the most important points. Better to have 4-5 clear, friendly points than 6+ dense ones.

Return ONLY valid JSON:
{{
  "slide_id": "{original_slide.slide_id}",
  "slide_type": "{original_slide.slide_type}",
  "title": "...",
  "content": ["Friendly point 1", "Friendly point 2", "Point 3", "Point 4 (if needed)", "Point 5 (if needed)"],
  "speaker_notes": "Warm, conversational explanation (4-6 sentences)",
  "image_query": "{original_slide.image_query}"
}}"""
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        try:
            data = json.loads(response.content)
        except:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0]
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0]
            data = json.loads(content.strip())
        
        return SlideContent(**data)

