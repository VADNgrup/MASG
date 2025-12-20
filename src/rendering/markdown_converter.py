from typing import List, Optional, Dict, Any
from src.models.slide import SlideContent
from src.rendering.layout_optimizer import determine_optimal_layout
from src.rendering.content_formatter import format_slide_content
import re

def escape_markdown(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\\", "\\\\")
    text = text.replace("*", "\\*")
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("(", "\\(")
    text = text.replace(")", "\\)")
    text = text.replace("`", "\\`")
    return text

def format_image_block(image_path: str, layout: str) -> str:
    if not image_path:
        return ""
    
    if layout == "two-cols":
        return f""":::
:right:

![Image]({image_path})
:::"""
    elif layout == "image-bottom":
        return f"\n\n<div class=\"flex justify-center mt-4\">\n  <img src=\"{image_path}\" class=\"max-h-96\" />\n</div>\n"
    else:
        return f"\n![Image]({image_path})\n"

def convert_slide_to_markdown(
    slide: SlideContent, 
    image_path: Optional[str] = None,
    optimization_metadata: Optional[Dict[str, Any]] = None
) -> str:
    slide_type = slide.slide_type.lower() if slide.slide_type else "default"
    
    if slide_type == "cover":
        layout = "cover"
    elif slide_type == "section":
        layout = "section"
    elif image_path:
        layout = "two-cols"
    else:
        layout = "default"
    
    frontmatter = f"---\ntheme: default\nlayout: {layout}\n"
    
    if slide.speaker_notes:
        notes_content = slide.speaker_notes.replace("\n", "\n  ")
        frontmatter += f"notes: |\n  {notes_content}\n"
    
    frontmatter += "---\n\n"
    
    if layout in ["cover", "section"]:
        if layout == "cover":
            frontmatter += f"# {slide.title}\n\n"
            if slide.content and len(slide.content) > 0:
                frontmatter += f"{slide.content[0]}\n\n"
        elif layout == "section":
            frontmatter += f"# {slide.title}\n\n"
            if slide.content and len(slide.content) > 0:
                frontmatter += f"{slide.content[0]}\n\n"
        return frontmatter
    
    title = f"# {slide.title}\n\n"
    
    content_types = None
    visual_hints = None
    if optimization_metadata:
        content_types = optimization_metadata.get("content_types")
        visual_hints = optimization_metadata.get("visual_hints")
    
    formatted_content = format_slide_content(slide.content, content_types, visual_hints)
    
    if layout == "two-cols" and image_path:
        content_lines = [f"- {bullet}" for bullet in formatted_content if bullet]
        content = "\n".join(content_lines) + "\n\n"
        image_block = f""":::
:right:

![Image]({image_path})
:::
"""
        return frontmatter + title + content + image_block
    else:
        content_lines = [f"- {bullet}" for bullet in formatted_content if bullet]
        content = "\n".join(content_lines) + "\n\n"
        return frontmatter + title + content

def convert_lecture_to_slidev(lecture_json: dict, image_handler, optimizer_agent=None) -> str:
    optimization_metadata_map = {}
    
    if optimizer_agent:
        try:
            optimized_json = optimizer_agent.optimize(lecture_json)
            optimization_results = optimized_json.get("optimization_metadata", [])
            for result in optimization_results:
                optimization_metadata_map[result["slide_id"]] = result["suggestions"]
        except Exception as e:
            print(f"Optimizer agent error: {e}, continuing without optimization")
    
    from src.rendering.slide_splitter import smart_split_slide
    from src.rendering.section_dividers import add_section_dividers
    
    all_slides = []
    all_slides_markdown = []
    
    for slide_data in lecture_json.get("slides", []):
        slide = SlideContent(**slide_data)
        optimization_metadata = optimization_metadata_map.get(slide.slide_id)
        
        split_slides = smart_split_slide(slide, optimization_metadata)
        
        for split_slide in split_slides:
            all_slides.append(split_slide)
            image_path = image_handler.resolve_image_path(split_slide.image) if split_slide.image else None
            
            split_optimization = optimization_metadata_map.get(split_slide.slide_id) or optimization_metadata
            
            slide_md = convert_slide_to_markdown(split_slide, image_path, split_optimization)
            all_slides_markdown.append(slide_md)
    
    slides_with_dividers = add_section_dividers(all_slides_markdown, all_slides)
    
    return "\n---\n\n".join(slides_with_dividers)

