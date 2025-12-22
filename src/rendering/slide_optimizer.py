from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
import json
from src.models.slide import SlideContent, LectureOutput
from src.utils.config import config

class SlideOptimizerAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
    
    def optimize(self, lecture_json: dict) -> dict:
        slides = lecture_json.get("slides", [])
        if not slides:
            return lecture_json
        
        optimization_results = []
        
        for slide_data in slides:
            slide = SlideContent(**slide_data)
            suggestions = self._analyze_slide(slide)
            optimization_results.append({
                "slide_id": slide.slide_id,
                "suggestions": suggestions
            })
        
        optimized_json = lecture_json.copy()
        optimized_json["optimization_metadata"] = optimization_results
        
        return optimized_json
    
    def _analyze_slide(self, slide: SlideContent) -> Dict[str, Any]:
        content_count = len(slide.content)
        total_chars = sum(len(bullet) for bullet in slide.content)
        avg_chars_per_bullet = total_chars / content_count if content_count > 0 else 0
        
        has_image = slide.image is not None
        image_content_type = slide.image.metadata.get("content_type") if slide.image else None
        
        content_preview = chr(10).join(slide.content[:3]) if slide.content else "No content"
        
        prompt = f"""Analyze this lecture slide and suggest optimizations for professional, friendly presentation.

SLIDE DATA:
Title: {slide.title}
Number of bullet points: {content_count}
Average characters per bullet: {avg_chars_per_bullet:.0f}
Has image: {has_image}
Image content type: {image_content_type or "none"}
Content preview:
{content_preview}

ANALYSIS TASKS:
1. Should this slide be split? (Consider: >5 bullets OR >75 chars/bullet average = too dense)
   - Maximum 5 bullets per slide for optimal readability
   - If 6+ bullets, recommend splitting
2. What's the optimal layout? (two-cols, image-bottom, centered, default)
3. Classify each bullet point type: "formula", "definition", "example", "property", "other"
4. Is the tone friendly and approachable? (Check for overly formal, rigid, or academic language)
5. Suggest visual enhancements (icons, colors, emphasis)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "should_split": true,
  "split_into": 2,
  "suggested_layout": "two-cols",
  "content_types": ["formula", "definition", "example"],
  "visual_hints": {{
    "use_icons": true,
    "use_colors": true,
    "emphasis_points": []
  }}
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1]
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group()
            
            suggestions = json.loads(content.strip())
            
            if content_count > 0:
                content_types = suggestions.get("content_types", [])
                if len(content_types) != content_count:
                    suggestions["content_types"] = self._fallback_content_types(slide.content)
            
            return suggestions
        except Exception as e:
            print(f"Optimizer Agent error for slide {slide.slide_id}: {e}")
            return self._fallback_suggestions(slide, content_count, has_image, image_content_type)
    
    def _fallback_content_types(self, content: List[str]) -> List[str]:
        types = []
        for bullet in content:
            if any(char in bullet for char in ["=", "≤", "≥", "∈", "π", "sin", "cos", "tan"]):
                types.append("formula")
            elif bullet.startswith("Tập") or bullet.startswith("Điều kiện") or "là" in bullet[:20]:
                types.append("definition")
            elif "Ví dụ" in bullet or "Example" in bullet:
                types.append("example")
            else:
                types.append("property")
        return types
    
    def _fallback_suggestions(self, slide: SlideContent, content_count: int, has_image: bool, image_content_type: Optional[str]) -> Dict[str, Any]:
        should_split = content_count > 5
        split_into = 2 if content_count <= 8 else 3
        
        if not has_image:
            layout = "centered" if content_count <= 3 else "default"
        elif image_content_type in ["table_image", "diagram"]:
            layout = "image-bottom"
        elif content_count <= 4:
            layout = "two-cols"
        else:
            layout = "image-bottom"
        
        return {
            "should_split": should_split,
            "split_into": split_into if should_split else 1,
            "suggested_layout": layout,
            "content_types": self._fallback_content_types(slide.content),
            "visual_hints": {
                "use_icons": True,
                "use_colors": True,
                "emphasis_points": []
            }
        }

