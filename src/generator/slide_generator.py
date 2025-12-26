import json
import argparse
import os
import shutil
from pathlib import Path
import sys

try:
    from src.generator.intermediate_format import transform_to_intermediate
    from src.generator.agents.layout_analyzer import LayoutAnalyzer
    from src.generator.agents.layout_selector import LayoutSelector
    from src.generator.agents.slide_decorator import SlideDecorator
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.generator.intermediate_format import transform_to_intermediate
    from src.generator.agents.layout_analyzer import LayoutAnalyzer
    from src.generator.agents.layout_selector import LayoutSelector
    from src.generator.agents.slide_decorator import SlideDecorator

def generate_slides(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides_data = data.get("slides", [])
    if not slides_data:
        print("No slides found in data.")
        return

    json_file = Path(json_path)
    lecture_id = json_file.stem.replace("lec_", "")
    
    assets_base = Path("data/assets")
    assets_source = None
    
    if assets_base.exists():
        for dir_path in assets_base.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith(lecture_id):
                assets_source = dir_path / "images"
                break
    
    assets_dest = Path("slidev/public/assets")
    
    if assets_dest.exists():
        for old_file in assets_dest.glob("*"):
            if old_file.is_file():
                old_file.unlink()
    
    assets_dest.mkdir(parents=True, exist_ok=True)
    
    image_ids = set()
    for slide in slides_data:
        image_data = slide.get("image")
        if isinstance(image_data, dict):
            image_id = image_data.get("image_id")
            if image_id:
                image_ids.add(image_id)
    
    if assets_source and assets_source.exists():
        for image_id in image_ids:
            for ext in ['.png', '.jpg', '.jpeg']:
                src_file = assets_source / f"{image_id}{ext}"
                if src_file.exists():
                    shutil.copy2(src_file, assets_dest / src_file.name)
                    break

    intermediate_slides = transform_to_intermediate(slides_data)
    
    analyzer = LayoutAnalyzer()
    intermediate_slides = analyzer.analyze(intermediate_slides)
    
    selector = LayoutSelector()
    intermediate_slides = selector.select_layouts(intermediate_slides)
    
    from src.generator.agents.theme_builder import ThemeBuilderAgent
    theme_builder = ThemeBuilderAgent()
    theme = theme_builder.build_theme(intermediate_slides)
    
    theme_css = theme_builder.generate_theme_css(theme, lecture_id, intermediate_slides)
    theme_css_path = Path("slidev/theme") / f"{lecture_id}.css"
    theme_css_path.parent.mkdir(parents=True, exist_ok=True)
    with open(theme_css_path, 'w', encoding='utf-8') as f:
        f.write(theme_css)
    
    decorator = SlideDecorator()
    intermediate_slides = decorator.decorate(intermediate_slides, theme)

    markdown_output = [
        f"<style src=\"./theme/{lecture_id}.css\"></style>",
    ]

    for i, slide in enumerate(intermediate_slides):
        md_chunk = _render_slide(slide, i)
        markdown_output.append(md_chunk)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_output))

def _render_slide(slide, index=0):
    layout = slide.selected_layout or "default"
    
    md_chunk = ""
    
    if index > 0:
        md_chunk += f"---\nlayout: {layout}\n"
        
        if slide.animations.get("transition"):
            md_chunk += f"transition: {slide.animations['transition']}\n"
        
        custom_class = "text-center" if slide.analyzed_type and slide.analyzed_type.value in ["intro", "statement", "conclusion"] else ""
        if custom_class:
            md_chunk += f"class: {custom_class}\n"
        
        image = slide.image_id or slide.image_url
        if image and layout in ["image-right", "image-left", "image"]:
            md_chunk += f'image: "{image}"\n'
        
        md_chunk += "---\n\n"
    
    bg = slide.decorations.get("background", {})
    if bg.get("type") == "gradient" and bg.get("value"):
        md_chunk += f'<div style="background: {bg["value"]}; padding: 2rem; border-radius: 12px; height: 100%;">\n\n'
    
    if layout == "cover":
        md_chunk += f"# {slide.title}\n\n"
        for item in slide.content:
            md_chunk += f"{item}\n\n"
    
    elif layout in ["center", "quote", "end"]:
        md_chunk += f"# {slide.title}\n\n"
        for item in slide.content:
            md_chunk += f"{item}\n\n"
    
    elif layout == "two-cols":
        md_chunk += f"# {slide.title}\n\n"
        mid = len(slide.content) // 2
        
        for item in slide.content[:mid]:
            md_chunk += f"- {item}\n"
        
        md_chunk += "\n::right::\n\n"
        
        for item in slide.content[mid:]:
            md_chunk += f"- {item}\n"
    
    elif layout in ["image-right", "image-left", "image"]:
        md_chunk += f"# {slide.title}\n\n"
        
        if slide.animations.get("use_v_click"):
            md_chunk += "<div v-click>\n\n"
        
        for item in slide.content:
            md_chunk += f"- {item}\n"
        
        if slide.animations.get("use_v_click"):
            md_chunk += "\n</div>\n"
    
    else:
        md_chunk += f"# {slide.title}\n\n"
        
        if slide.animations.get("use_v_click"):
            md_chunk += "<div v-click>\n\n"
        
        for item in slide.content:
            md_chunk += f"- {item}\n"
        
        if slide.animations.get("use_v_click"):
            md_chunk += "\n</div>\n"
    
    if bg.get("type") == "gradient" and bg.get("value"):
        md_chunk += "\n</div>\n"
    
    return md_chunk

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_md")
    args = parser.parse_args()
    generate_slides(args.input_json, args.output_md)
