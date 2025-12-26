from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
from src.generator.intermediate_format import IntermediateSlide
from src.utils.config import config

class ThemeBuilderAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.7)
        self.model = model
    
    def build_theme(self, slides: List[IntermediateSlide]) -> Dict[str, Any]:
        lecture_title = slides[0].title if slides else "Lecture"
        topics = [s.title for s in slides[:5]]
        
        prompt = f"""You are a professional presentation designer. Create a beautiful, cohesive theme for this lecture.

Lecture Title: {lecture_title}
Topics: {', '.join(topics)}

IMPORTANT: Prioritize WHITE and BLUE color schemes for a clean, professional look.

Analyze the content and create a theme with:

1. **Color Palette** (PREFER WHITE & BLUE):
   - primary: Blue shade (#2563eb, #3b82f6, #60a5fa, or similar)
   - secondary: Lighter blue or complementary (#93c5fd, #dbeafe, or teal)
   - accent: Accent blue or green (#0ea5e9, #06b6d4, #10b981)
   - background: White or very light blue (#ffffff, #f8fafc, #f0f9ff)

2. **Typography**:
   - heading_font: Clean sans-serif (Inter, Poppins, or Montserrat)
   - body_font: Readable sans-serif (Inter or Open Sans)

3. **Visual Style**:
   - style: "professional" | "modern" | "minimal" | "clean"
   - background_pattern: "none" | "dots" | "grid" | "subtle-gradient"

4. **Mood**:
   - tone: "professional" | "calm" | "clear" | "trustworthy"

EXAMPLES of good white/blue themes:
- Primary: #2563eb, Secondary: #93c5fd, Accent: #0ea5e9, Background: #ffffff
- Primary: #3b82f6, Secondary: #dbeafe, Accent: #10b981, Background: #f8fafc

Return ONLY valid JSON:
{{
  "name": "Professional Blue Theme",
  "colors": {{
    "primary": "#2563eb",
    "secondary": "#93c5fd",
    "accent": "#0ea5e9",
    "background": "#ffffff"
  }},
  "typography": {{
    "heading_font": "Inter",
    "body_font": "Inter"
  }},
  "visual_style": {{
    "style": "professional",
    "background_pattern": "dots"
  }},
  "mood": {{
    "tone": "professional"
  }}
}}"""

        response = self.llm.invoke(prompt)
        
        try:
            theme_data = json.loads(response.content)
        except:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            theme_data = json.loads(content.strip())
        
        return theme_data
    
    def generate_theme_css(self, theme: Dict[str, Any], lecture_id: str) -> str:
        colors = theme.get("colors", {})
        typography = theme.get("typography", {})
        visual_style = theme.get("visual_style", {})
        
        bg_color = colors.get('background', '#ffffff')
        is_dark_bg = 'gradient' in bg_color.lower() or any(c in bg_color.lower() for c in ['#667', '#764', '#333', '#222'])
        
        css = f"""@import url('https://fonts.googleapis.com/css2?family={typography.get('heading_font', 'Inter').replace(' ', '+')}:wght@300;400;600;700&family={typography.get('body_font', 'Inter').replace(' ', '+')}:wght@300;400;600&display=swap');

:root {{
  --theme-primary: {colors.get('primary', '#2563eb')};
  --theme-secondary: {colors.get('secondary', '#93c5fd')};
  --theme-accent: {colors.get('accent', '#0ea5e9')};
  --theme-background: {bg_color};
}}

html {{
  font-family: '{typography.get('body_font', 'Inter')}', sans-serif;
  background: var(--theme-background);
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: '{typography.get('heading_font', 'Inter')}', sans-serif;
  font-weight: 700;
}}

h1 {{
  font-size: 2.5rem;
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}

.slidev-layout.cover {{
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  color: white;
}}

.slidev-layout.cover h1 {{
  background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 3.5rem;
}}

li::before {{
  color: var(--theme-primary);
}}

.slidev-layout {{
  background: var(--theme-background);
}}
"""
        
        if visual_style.get('background_pattern') == 'dots':
            css += """
.slidev-layout:not(.cover)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(circle, var(--theme-primary) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.05;
  pointer-events: none;
  z-index: 0;
}
"""
        elif visual_style.get('background_pattern') == 'grid':
            css += """
.slidev-layout:not(.cover)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(var(--theme-primary) 1px, transparent 1px),
    linear-gradient(90deg, var(--theme-primary) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.03;
  pointer-events: none;
  z-index: 0;
}
"""
        
        return css
