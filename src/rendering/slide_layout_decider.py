from langchain_openai import ChatOpenAI
from typing import Dict, Any
import json
from src.models.slide import SlideContent

class SlideLayoutDecider:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
    
    def decide_layout(self, slide: SlideContent, has_image: bool = False) -> Dict[str, Any]:
        content_preview = "\n".join(slide.content[:4]) if slide.content else ""
        content_count = len(slide.content)

        prompt = f"""You are helping design professional presentation slides.

Slide title: {slide.title}
Number of bullet points: {content_count}
Has image: {has_image}
First bullets:
{content_preview}

Choose the best layout and density:
- layout: one of ["two-cols", "default", "center"]
  - "two-cols": text on the left, visual or extra content on the right
  - "default": single column content
  - "center": centered, good for summary / key message
- density: one of ["low", "medium", "high"]
  - low: 1–2 key blocks, lots of whitespace
  - medium: 3–4 blocks
  - high: 5+ blocks (split into grid)

Return ONLY valid JSON, no markdown, in this format:
{{
  "layout": "two-cols",
  "density": "medium",
  "reason": "Short explanation"
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
            
            result = json.loads(content.strip())

            layout = result.get("layout", "default")
            if layout not in ["two-cols", "default", "center"]:
                layout = "default"

            density = result.get("density", "medium")
            if density not in ["low", "medium", "high"]:
                density = "medium"

            return {
                "layout": layout,
                "density": density,
                "reason": result.get("reason", ""),
            }
            
        except Exception as e:
            print(f"SlideLayoutDecider error: {e}, using fallback")
            return self._fallback_decision(slide, has_image, content_count)
    
    def _fallback_decision(self, slide: SlideContent, has_image: bool, content_count: int) -> Dict[str, Any]:
        if has_image or content_count >= 6:
            layout = "two-cols"
            density = "high"
        elif content_count <= 2:
            layout = "center"
            density = "low"
        else:
            layout = "default"
            density = "medium"

        return {
            "layout": layout,
            "density": density,
            "reason": "Fallback decision",
        }

