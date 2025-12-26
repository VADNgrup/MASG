from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
from src.generator.intermediate_format import IntermediateSlide, SlideType
from src.utils.config import config

class SlideDecorator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.6)
        self.model = model
    
    def decorate(self, slides: List[IntermediateSlide], theme: Dict[str, Any]) -> List[IntermediateSlide]:
        for i, slide in enumerate(slides):
            slide.theme = theme
            slide.animations = self._generate_animations(slide)
            slide.decorations = self._generate_decorations_llm(slide, theme, i, len(slides))
        
        return slides
    
    def _generate_animations(self, slide: IntermediateSlide) -> Dict[str, Any]:
        animations = {
            "transition": self._select_transition(slide),
            "use_v_click": self._should_use_v_click(slide),
            "entrance": "fade-in",
            "emphasis": None
        }
        
        return animations
    
    def _select_transition(self, slide: IntermediateSlide) -> str:
        if slide.analyzed_type == SlideType.INTRO:
            return "fade-out"
        elif slide.analyzed_type == SlideType.STATEMENT:
            return "fade"
        elif slide.analyzed_type == SlideType.CONCLUSION:
            return "slide-up"
        else:
            return "slide-left"
    
    def _should_use_v_click(self, slide: IntermediateSlide) -> bool:
        if slide.analyzed_type == SlideType.INTRO:
            return False
        
        if slide.analyzed_type == SlideType.STATEMENT:
            return False
        
        if slide.bullet_count >= 3 and slide.bullet_count <= 5:
            return True
        
        return False
    
    def _generate_decorations_llm(self, slide: IntermediateSlide, theme: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
        prompt = f"""You are a presentation designer. Add visual decorations to make this slide beautiful and engaging.

Slide #{index + 1}/{total}
Title: {slide.title}
Type: {slide.analyzed_type.value if slide.analyzed_type else 'content'}
Layout: {slide.selected_layout}
Has Image: {slide.has_image}
Theme Style: {theme.get('visual_style', {}).get('style', 'modern')}
Theme Mood: {theme.get('mood', {}).get('tone', 'professional')}

Choose decorations that match the theme and enhance the slide:

1. **Background**: 
   - type: "solid" | "gradient" | "pattern" | "image"
   - value: CSS value or description

2. **Shapes** (decorative geometric elements):
   - positions: ["top-right", "bottom-left", etc.]
   - shapes: ["circle", "square", "triangle", "blob"]

3. **Icons** (if relevant to content):
   - icons: ["lightbulb", "chart", "book", etc.] or []

4. **Effects**:
   - shadow: "subtle" | "medium" | "strong" | "none"
   - border: "none" | "accent" | "gradient"

Return ONLY valid JSON:
{{
  "background": {{
    "type": "gradient",
    "value": "linear-gradient(135deg, rgba(91, 141, 239, 0.1) 0%, rgba(79, 184, 179, 0.1) 100%)"
  }},
  "shapes": {{
    "positions": ["top-right"],
    "shapes": ["circle"]
  }},
  "icons": [],
  "effects": {{
    "shadow": "subtle",
    "border": "none"
  }}
}}"""

        try:
            response = self.llm.invoke(prompt)
            
            try:
                decorations = json.loads(response.content)
            except:
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                decorations = json.loads(content.strip())
            
            return decorations
        except Exception as e:
            return {
                "background": {"type": "solid", "value": "transparent"},
                "shapes": {"positions": [], "shapes": []},
                "icons": [],
                "effects": {"shadow": "none", "border": "none"}
            }
