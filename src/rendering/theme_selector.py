from langchain_openai import ChatOpenAI
from typing import Dict, Any
import json

class ThemeSelector:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.default_theme = "seriph"
    
    def select_theme(self, lecture_json: dict) -> str:
        try:
            slides = lecture_json.get("slides", [])
            if not slides:
                return self.default_theme
            
            sample_slides = slides[:3]
            sample_content = "\n\n".join([
                f"Slide: {slide.get('title', '')}\n" + 
                "\n".join(slide.get('content', [])[:3])
                for slide in sample_slides
            ])
            
            metadata = lecture_json.get("metadata", {})
            total_slides = metadata.get("total_slides", len(slides))
            
            prompt = f"""Analyze this lecture presentation and recommend the best Slidev theme.

Sample content:
{sample_content}

Total slides: {total_slides}

Available themes:
1. "seriph" - Elegant, professional, serif fonts. Best for: Academic/formal presentations, theory-heavy content, formal reports
2. "default" - Clean, modern, sans-serif. Best for: Technical content, practical guides, code examples, balanced presentations
3. "apple-basic" - Minimal, Apple-style design. Best for: Product presentations, modern/creative content, visual-heavy slides

Analyze based on:
- Tone: Is it formal/academic or casual/practical?
- Content structure: Theory-heavy or hands-on/practical?
- Visual needs: Text-heavy or balanced with visuals?
- DO NOT analyze by domain (math, history, etc.) - be generic!

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "theme": "seriph",
  "reason": "Brief explanation"
}}"""
            
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
            theme = result.get("theme", self.default_theme)
            
            valid_themes = ["seriph", "default", "apple-basic"]
            if theme not in valid_themes:
                theme = self.default_theme
            
            print(f"ThemeSelector: Selected '{theme}' - {result.get('reason', 'No reason provided')}")
            return theme
            
        except Exception as e:
            print(f"ThemeSelector error: {e}, using default theme")
            return self.default_theme
    
    def get_theme_config(self, theme: str) -> Dict[str, Any]:
        configs = {
            "seriph": {
                "highlighter": "shiki",
                "lineNumbers": False,
                "transition": "slide-left"
            },
            "default": {
                "highlighter": "shiki",
                "lineNumbers": True,
                "transition": "fade-out"
            },
            "apple-basic": {
                "highlighter": "shiki",
                "lineNumbers": False,
                "transition": "slide-up"
            }
        }
        return configs.get(theme, configs["seriph"])

