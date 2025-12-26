from langchain_openai import ChatOpenAI
from typing import List
import json
from src.generator.intermediate_format import IntermediateSlide, SlideType, ContentDensity
from src.utils.config import config

class LayoutAnalyzer:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model
    
    def analyze(self, slides: List[IntermediateSlide]) -> List[IntermediateSlide]:
        for i, slide in enumerate(slides):
            slide.analyzed_type = self._classify_slide_type_llm(slide, i, len(slides))
            slide.content_density = self._compute_density(slide)
            slide.suggested_layouts = self._suggest_layouts(slide)
        
        return slides
    
    def _classify_slide_type_llm(self, slide: IntermediateSlide, index: int, total: int) -> SlideType:
        if index == 0:
            return SlideType.INTRO
        
        if index == total - 1 and any(keyword in slide.title.lower() for keyword in ["kết luận", "tổng kết", "summary", "conclusion"]):
            return SlideType.CONCLUSION
        
        prompt = f"""Analyze this slide and classify its type.

Slide Title: {slide.title}
Content: {' | '.join(slide.content[:3])}
Has Image: {slide.has_image}
Bullet Count: {slide.bullet_count}
Text Length: {slide.text_length}

Classify into ONE of these types:
- INTRO: Introduction or opening slide
- VISUAL_FOCUS: Slide where image is the main focus, minimal text
- STATEMENT: Short impactful statement or key message (< 100 chars)
- COMPARISON: Comparing two or more things
- CONTENT_HEAVY: Detailed content with multiple points
- CONCLUSION: Summary or closing slide

Return ONLY the type name (e.g., "VISUAL_FOCUS")."""

        response = self.llm.invoke(prompt)
        type_str = response.content.strip().upper().replace("SLIDETYPE.", "")
        
        try:
            return SlideType[type_str]
        except KeyError:
            return SlideType.CONTENT_HEAVY
    
    def _compute_density(self, slide: IntermediateSlide) -> ContentDensity:
        if slide.text_length < 150:
            return ContentDensity.LOW
        elif slide.text_length < 400:
            return ContentDensity.MEDIUM
        else:
            return ContentDensity.HIGH
    
    def _suggest_layouts(self, slide: IntermediateSlide) -> List[str]:
        suggestions = []
        
        if slide.analyzed_type == SlideType.INTRO:
            suggestions = ["cover"]
        
        elif slide.analyzed_type == SlideType.CONCLUSION:
            suggestions = ["end", "center"]
        
        elif slide.analyzed_type == SlideType.STATEMENT:
            suggestions = ["center", "quote"]
        
        elif slide.analyzed_type == SlideType.VISUAL_FOCUS:
            if slide.has_image:
                suggestions = ["image-right", "image-left", "image"]
            else:
                suggestions = ["center"]
        
        elif slide.analyzed_type == SlideType.COMPARISON:
            suggestions = ["two-cols", "default"]
        
        elif slide.analyzed_type == SlideType.CONTENT_HEAVY:
            if slide.has_image:
                suggestions = ["image-right", "default"]
            else:
                suggestions = ["default"]
        
        else:
            suggestions = ["default"]
        
        return suggestions
