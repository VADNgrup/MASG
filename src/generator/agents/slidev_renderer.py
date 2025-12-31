from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from src.generator.agents.template_matcher import TemplateMatcher

class SlidevRenderer:
    def __init__(self, template_name: str = "dark_modern"):
        self.template_name = template_name
        template_dir = Path(f"data/templates/{template_name}")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        self.matcher = TemplateMatcher(template_name=template_name)
    
    def render_slidev(self, data: Dict[str, Any]) -> str:
        """Render slides using LLM-based template matching."""
        print("\n" + "="*60)
        print("SLIDEV RENDERER - Template Matching")
        print("="*60)
        
        slides_data = data.get("slides", [])
        
        enriched_slides = self.matcher.match_all(slides_data)
        
        rendered_slides = []
        for slide in enriched_slides:
            component = slide.get("_component", "visual")
            template_file = f"{component}.md"
            
            clean_slide = {k: v for k, v in slide.items() if not k.startswith("_")}
            
            rendered = self._render_template(template_file, clean_slide)
            rendered_slides.append(rendered)
        
        print(f"\n✓ Rendered {len(rendered_slides)} slides")
        print("="*60)
        
        return "\n\n".join(rendered_slides)
    
    def _render_template(self, template_name: str, slide: Dict[str, Any]) -> str:
        """Render a slide using Jinja2 template."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**slide).strip()
        except Exception as e:
            print(f"Failed to render {template_name}: {e}")
            return f"<!-- Error rendering {template_name}: {e} -->"
    
    def save_to_slidev(self, markdown_content: str, output_path: str = "slidev/slides.md") -> str:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_content, encoding='utf-8')
        return str(output_file)
