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
        
        system_prompt = f"""You are refining a lecture slide to add missing information.

The original slide is incomplete. Your task:
1. Keep all existing good content
2. ADD the missing information listed below
3. Expand speaker notes with the missing context
4. Ensure comprehensive coverage

Write in {language} language.

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
- 6-8 bullet points including both original AND missing information
- Expanded speaker notes (5-7 sentences) covering everything
- Same image_query

Return ONLY valid JSON:
{{
  "slide_id": "{original_slide.slide_id}",
  "slide_type": "{original_slide.slide_type}",
  "title": "...",
  "content": ["...", "..."],
  "speaker_notes": "...",
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

