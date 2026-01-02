from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import json
from jinja2 import Environment, FileSystemLoader
from src.generator.agents.asset_manager import AssetResolver


def latex_wrap(value):
    if not value or not isinstance(value, str):
        return value
    if value.startswith('$') and value.endswith('$'):
        return value
    if '\\' in value or '^{' in value or '_{' in value:
        return f'${value}$'
    return value


def latex_inline(value):
    """Wrap LaTeX expressions that aren't already wrapped with $"""
    if not value or not isinstance(value, str):
        return value
    
    if value.strip().startswith('$'):
        return value
    
    # Check if entire value is a LaTeX expression
    stripped = value.strip()
    if stripped.startswith('\\') or '^{' in stripped or '_{' in stripped:
        # Entire cell is LaTeX - wrap whole thing
        return f'${stripped}$'
    
    # Check for patterns like "30^{\circ}" at start
    if re.match(r'^\d+\^', stripped):
        return f'${stripped}$'
    
    return value


def auto_latex_wrap(data):
    if isinstance(data, str):
        return latex_inline(data)
    elif isinstance(data, list):
        return [auto_latex_wrap(item) for item in data]
    elif isinstance(data, dict):
        return {k: auto_latex_wrap(v) for k, v in data.items()}
    return data


class ThemeConfig:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @property
    def layout(self) -> str:
        return self.config.get("layout", "default")
    
    @property
    def base_class(self) -> str:
        return self.config.get("base_class", "")
    
    @property
    def colors(self) -> Dict[str, str]:
        return self.config.get("colors", {})
    
    @property
    def components(self) -> Dict[str, str]:
        return self.config.get("components", {})
    
    @property
    def animations(self) -> Dict[str, str]:
        return self.config.get("animations", {})
    
    @property
    def icons(self) -> Dict[str, str]:
        return self.config.get("icons", {})
    
    @property
    def defaults(self) -> Dict[str, str]:
        return self.config.get("defaults", {})
    
    def get_default_category(self, slide_type: str) -> str:
        key = f"category_{slide_type}"
        return self.defaults.get(key, slide_type.title())
    
    def to_template_vars(self) -> Dict[str, Any]:
        return {
            "theme": {
                "layout": self.layout,
                "base_class": self.base_class,
                "colors": self.colors,
                "components": self.components,
                "animations": self.animations,
                "icons": self.icons,
                "defaults": self.defaults
            }
        }


class SlidevRenderer:
    def __init__(self, template_name: str = "dark_modern", lecture_id: Optional[str] = None):
        self.template_name = template_name
        template_dir = Path(f"data/templates/{template_name}")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        self.env.filters['latex'] = latex_wrap
        self.env.filters['latex_inline'] = latex_inline
        
        self.theme = ThemeConfig(template_dir / "config.json")
        
        self.asset_resolver = AssetResolver()
        if lecture_id:
            self.asset_resolver.set_lecture_context(lecture_id)
        
        self.available_templates = self._discover_templates(template_dir)
    
    def _discover_templates(self, template_dir: Path) -> set:
        templates = set()
        for f in template_dir.glob("*.md"):
            if f.stem != "config":
                templates.add(f.stem)
        return templates
    
    def set_lecture_context(self, lecture_id: str):
        self.asset_resolver.set_lecture_context(lecture_id)
    
    def render_slidev(self, data: Dict[str, Any]) -> str:
        print("\n" + "="*60)
        print("SLIDEV RENDERER")
        print("="*60)
        
        slides_data = data.get("slides", [])
        
        rendered_slides = []
        for idx, slide in enumerate(slides_data):
            slide_type = slide.get("slide_type", "visual")
            
            if slide_type not in self.available_templates:
                print(f"  [{idx+1}] Unknown template '{slide_type}', falling back to 'visual'")
                slide_type = "visual"
            
            template_file = f"{slide_type}.md"
            
            processed_slide = self._process_slide_data(slide)
            
            rendered = self._render_template(template_file, processed_slide)
            rendered_slides.append(rendered)
            
            print(f"  [{idx+1}] {slide.get('title', 'Untitled')[:40]} → {slide_type}")
        
        print(f"\n✓ Rendered {len(rendered_slides)} slides")
        print("="*60)
        
        return "\n\n".join(rendered_slides)
    
    def _process_slide_data(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        slide_type = slide.get("slide_type", "visual")
        processed = {}
        skip_latex_fields = ["title", "category", "left_title", "right_title", "badge", "image", "formulas"]
        
        for key, value in slide.items():
            if key == "slide_type":
                continue
            if key == "image" and value:
                processed[key] = self.asset_resolver.resolve(value)
            elif key in skip_latex_fields:
                processed[key] = value
            else:
                processed[key] = auto_latex_wrap(value)
        
        if "category" not in processed or not processed.get("category"):
            processed["category"] = self.theme.get_default_category(slide_type)
        
        return processed
    
    def _render_template(self, template_name: str, slide: Dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            
            context = {**slide, **self.theme.to_template_vars()}
            return template.render(**context).strip()
        except Exception as e:
            print(f"  ✗ Failed to render {template_name}: {e}")
            return f"---\nlayout: center\n---\n\n# {slide.get('title', 'Error')}\n\nTemplate render error: {e}"
    
    def save_to_slidev(self, markdown_content: str, output_path: str = "slidev/slides.md") -> str:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_content, encoding='utf-8')
        return str(output_file)
