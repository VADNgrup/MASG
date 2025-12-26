from langchain_openai import ChatOpenAI
from typing import List, Optional
import json
from src.generator.intermediate_format import IntermediateSlide, SlideType
from src.utils.config import config

class LayoutSelector:
    
    def __init__(self, use_llm_fallback: bool = True, model: str = "gpt-4o-mini"):
        self.use_llm_fallback = use_llm_fallback
        self.llm = ChatOpenAI(model=model, temperature=0.1) if use_llm_fallback else None
        self.layout_history = []
    
    def select_layouts(self, slides: List[IntermediateSlide]) -> List[IntermediateSlide]:
        for i, slide in enumerate(slides):
            slide.selected_layout = self._select_best_layout(slide, i)
            self.layout_history.append(slide.selected_layout)
        
        return slides
    
    def _select_best_layout(self, slide: IntermediateSlide, index: int) -> str:
        if not slide.suggested_layouts:
            return "default"
        
        primary_suggestion = slide.suggested_layouts[0]
        
        if len(slide.suggested_layouts) == 1:
            return primary_suggestion
        
        if self._should_avoid_repetition(primary_suggestion):
            if len(slide.suggested_layouts) > 1:
                return slide.suggested_layouts[1]
        
        if self.use_llm_fallback and len(slide.suggested_layouts) > 1:
            if slide.analyzed_type in [SlideType.VISUAL_FOCUS, SlideType.COMPARISON]:
                return self._select_with_llm(slide)
        
        return primary_suggestion
    
    def _select_with_llm(self, slide: IntermediateSlide) -> str:
        prompt = f"""Choose the BEST Slidev layout for this slide.

Title: {slide.title}
Content: {' | '.join(slide.content[:3])}
Has Image: {slide.has_image}
Slide Type: {slide.analyzed_type.value}

Available layouts: {', '.join(slide.suggested_layouts)}

Slidev layout descriptions:
- image-right: Image on right, text on left
- image-left: Image on left, text on right
- two-cols: Two columns for comparison
- center: Centered content for impact
- default: Standard bullet list

Return ONLY the layout name (e.g., "image-right")."""

        try:
            response = self.llm.invoke(prompt)
            selected = response.content.strip().lower()
            
            if selected in slide.suggested_layouts:
                return selected
        except:
            pass
        
        return slide.suggested_layouts[0]
    
    def _should_avoid_repetition(self, layout: str) -> bool:
        if len(self.layout_history) < 2:
            return False
        
        recent_layouts = self.layout_history[-2:]
        
        if all(l == layout for l in recent_layouts):
            return True
        
        return False
