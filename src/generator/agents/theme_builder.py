from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
import random
from src.generator.intermediate_format import IntermediateSlide
from src.utils.config import config
from src.generator.design.tokens import DesignTokens, DesignStyle
from src.generator.design.generative_css import GenerativeStyleAgent

class ThemeBuilderAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.7)
        self.model = model
        self.generative_css = GenerativeStyleAgent()
    
    def build_theme(self, slides: List[IntermediateSlide]) -> Dict[str, Any]:
        palettes = DesignTokens.get_all_palettes(DesignStyle.PROFESSIONAL_MINIMAL)
        typography_pairs = DesignTokens.get_all_typography(DesignStyle.PROFESSIONAL_MINIMAL)
        layout_patterns = DesignTokens.get_all_layouts(DesignStyle.PROFESSIONAL_MINIMAL)
        
        selected_palette = random.choice(palettes)
        selected_typography = random.choice(typography_pairs)
        selected_layout = random.choice(layout_patterns)
        
        theme = {
            "name": f"{selected_palette.name} Theme",
            "colors": selected_palette.to_dict(),
            "typography": {
                "heading_font": selected_typography.heading_font,
                "body_font": selected_typography.body_font,
                "scale": selected_typography.scale,
                "sizes": selected_typography.get_sizes()
            },
            "visual_style": {
                "style": "professional",
                "background_pattern": random.choice(["dots", "grid", "none"])
            },
            "layout_pattern": {
                "name": selected_layout.name,
                "type": selected_layout.type,
                "proportions": selected_layout.proportions,
                "whitespace": selected_layout.whitespace,
                "alignment": selected_layout.alignment
            },
            "mood": {
                "tone": "professional"
            }
        }
        
        return theme
    
    def generate_theme_css(self, theme: Dict[str, Any], lecture_id: str, slides: List[IntermediateSlide]) -> str:
        """Generate advanced CSS using generative agent"""
        
        from src.generator.design.tokens import ColorPalette, TypographyPair, LayoutPattern
        
        colors = theme.get("colors", {})
        palette = ColorPalette(
            name=colors.get("name", "Custom"),
            primary=colors.get("primary", "#2563eb"),
            secondary=colors.get("secondary", "#93c5fd"),
            accent=colors.get("accent", "#0ea5e9"),
            background=colors.get("background", "#ffffff"),
            text_primary=colors.get("text_primary", "#1a1a1a"),
            text_secondary=colors.get("text_secondary", "#6b7280")
        )
        
        typo = theme.get("typography", {})
        typography = TypographyPair(
            name="Custom",
            heading_font=typo.get("heading_font", "Inter"),
            body_font=typo.get("body_font", "Inter"),
            scale=typo.get("scale", 1.25)
        )
        
        layout_data = theme.get("layout_pattern", {})
        layout_pattern = LayoutPattern(
            name=layout_data.get("name", "Default"),
            type=layout_data.get("type", "balanced"),
            proportions=layout_data.get("proportions", {}),
            whitespace=layout_data.get("whitespace", "balanced"),
            alignment=layout_data.get("alignment", "left")
        )
        
        content_summary = f"Lecture with {len(slides)} slides. Topics: " + ", ".join([s.title for s in slides[:3]])
        
        generated_css = self.generative_css.generate_presentation_css(
            palette=palette,
            typography=typography,
            layout_pattern=layout_pattern,
            content_summary=content_summary
        )
        
        if "```css" in generated_css:
            generated_css = generated_css.split("```css")[1].split("```")[0]
        elif "```" in generated_css:
            generated_css = generated_css.split("```")[1].split("```")[0]
        
        return generated_css.strip()
