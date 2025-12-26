from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
from src.utils.config import config
from src.generator.design.tokens import (
    DesignTokens, ColorPalette, TypographyPair, 
    LayoutPattern, DesignStyle
)
from src.generator.design.elite_examples import EliteExamplesLibrary

class GenerativeStyleAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.8)
        self.model = model
    
    def generate_presentation_css(
        self,
        palette: ColorPalette,
        typography: TypographyPair,
        layout_pattern: LayoutPattern,
        content_summary: str
    ) -> str:
        elite_examples = EliteExamplesLibrary.get_examples_for_llm("professional_minimal")
        
        type_sizes = typography.get_sizes()
        
        prompt = f"""You are an expert CSS designer. Generate beautiful, modern CSS for a presentation.

DESIGN TOKENS TO USE:

Color Palette: {palette.name}
- Primary: {palette.primary}
- Secondary: {palette.secondary}
- Accent: {palette.accent}
- Background: {palette.background}
- Text Primary: {palette.text_primary}
- Text Secondary: {palette.text_secondary}

Typography: {typography.name}
- Heading Font: {typography.heading_font}
- Body Font: {typography.body_font}
- Type Scale: {type_sizes}

Layout Pattern: {layout_pattern.name}
- Type: {layout_pattern.type}
- Proportions: {layout_pattern.proportions}
- Whitespace: {layout_pattern.whitespace}
- Alignment: {layout_pattern.alignment}

Content Summary: {content_summary}

ELITE EXAMPLES FOR INSPIRATION:
{elite_examples}

REQUIREMENTS:
1. Use modern CSS features:
   - CSS Grid for layouts
   - CSS Custom Properties (variables)
   - Flexbox for alignment
   - Backdrop filters for glassmorphism effects
   - Clip-path for unique shapes
   - CSS animations (subtle, professional)

2. Apply design principles:
   - Golden ratio for proportions
   - Consistent spacing (multiples of 8px or 16px)
   - High contrast for accessibility (WCAG AA)
   - Visual hierarchy (size, color, weight)
   - Generous whitespace

3. Professional effects:
   - Gradient text for headings
   - Subtle shadows for depth
   - Rounded corners (8px, 12px, 16px)
   - Smooth transitions
   - Glassmorphism for cards/overlays

4. Must include:
   - Root variables
   - Base typography styles
   - Layout utilities
   - Component styles (cards, buttons, etc.)
   - Responsive considerations
   - Animation keyframes

Return ONLY the CSS code, no explanations. Make it production-ready and beautiful.
"""

        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def generate_slide_specific_styles(
        self,
        slide_type: str,
        has_image: bool,
        content_length: int,
        theme_colors: Dict[str, str]
    ) -> Dict[str, str]:
        """Generate specific styles for individual slides"""
        
        prompt = f"""Generate specific CSS styles for this slide:

Slide Type: {slide_type}
Has Image: {has_image}
Content Length: {content_length} characters
Theme Colors: {json.dumps(theme_colors, indent=2)}

Return JSON with:
{{
  "background": "CSS background value",
  "padding": "CSS padding value",
  "text_align": "left|center|right",
  "special_effects": ["effect1", "effect2"]
}}

Make it beautiful and appropriate for the slide type."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except:
            return {
                "background": theme_colors.get("background", "#ffffff"),
                "padding": "3rem",
                "text_align": "left",
                "special_effects": []
            }
