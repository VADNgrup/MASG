from typing import List, Optional, Dict, Any
from src.models.slide import SlideContent
from src.rendering.content_formatter import ContentFormatter
from src.rendering.slide_layout_decider import SlideLayoutDecider
from src.rendering.smart_slide_splitter import SmartSlideSplitter

class MarkdownConverter:
    def __init__(self):
        self.formatter = ContentFormatter()
        self.layout_decider = SlideLayoutDecider()
        self.splitter = SmartSlideSplitter()
    
    def convert_slide_to_markdown(
        self,
        slide: SlideContent,
        image_path: Optional[str] = None,
        optimization_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        slide_type = slide.slide_type.lower() if slide.slide_type else "default"
        
        if slide_type in ["cover", "section"]:
            return self._format_special_slide(slide, slide_type)
        
        layout_decision = self.layout_decider.decide_layout(slide, bool(image_path))
        
        content_types = None
        if optimization_metadata:
            content_types = optimization_metadata.get("content_types")
        
        layout = layout_decision["layout"]
        density = layout_decision.get("density", "medium")

        frontmatter = f"""---
layout: {layout}
transition: slide-left
"""
        
        if slide.speaker_notes:
            notes_content = slide.speaker_notes.replace("\n", "\n  ")
            frontmatter += f"notes: |\n  {notes_content}\n"
        
        frontmatter += "---\n\n"
        
        title = f"# {slide.title}\n\n"

        if layout == "two-cols":
            return self._format_two_cols(slide, image_path, content_types, frontmatter, title, density)
        if layout == "center":
            return self._format_center(slide, content_types, frontmatter, title)
        if density == "high":
            return self._format_grid(slide, content_types, frontmatter, title)
        return self._format_default(slide, content_types, frontmatter, title)
    
    def _format_special_slide(self, slide: SlideContent, slide_type: str) -> str:
        if slide_type == "cover":
            return ""
        elif slide_type == "section":
            return ""
        return ""
    
    def _format_two_cols(
        self,
        slide: SlideContent,
        image_path: Optional[str],
        content_types: Optional[List[str]],
        frontmatter: str,
        title: str,
        density: str
    ) -> str:
        split_point = len(slide.content) // 2
        
        left_boxes, right_boxes = self.formatter.format_for_two_cols(
            slide.content,
            content_types,
            split_point
        )
        
        left_content = f'<div class="mt-8 space-y-6">\n\n'
        left_content += "\n\n".join(left_boxes)
        left_content += "\n\n</div>\n\n"
        
        right_content = f'<div class="ml-8 mt-8">\n\n'
        
        if image_path:
            right_content += f'<div class="mb-6">\n<img src="{image_path}" class="rounded-2xl shadow-lg" />\n</div>\n\n'
        
        if right_boxes:
            right_content += '<div class="space-y-6">\n\n'
            right_content += "\n\n".join(right_boxes)
            right_content += "\n\n</div>\n\n"
        
        right_content += "</div>\n"
        
        return frontmatter + title + left_content + "::right::\n\n" + right_content
    
    def _format_grid(
        self,
        slide: SlideContent,
        content_types: Optional[List[str]],
        frontmatter: str,
        title: str,
    ) -> str:
        boxes = self.formatter.format_bullets_with_boxes(slide.content, content_types)
        
        grid_content = '<div class="grid grid-cols-2 gap-8 mt-8">\n\n<div>\n\n'
        
        mid = len(boxes) // 2
        grid_content += "\n\n".join(boxes[:mid])
        grid_content += "\n\n</div>\n\n<div>\n\n"
        grid_content += "\n\n".join(boxes[mid:])
        grid_content += "\n\n</div>\n\n</div>\n"
        
        return frontmatter + title + grid_content

    def _format_center(
        self,
        slide: SlideContent,
        content_types: Optional[List[str]],
        frontmatter: str,
        title: str,
    ) -> str:
        boxes = self.formatter.format_bullets_with_boxes(slide.content, content_types)

        content = '<div class="mt-10 max-w-3xl mx-auto space-y-6 text-center">\n\n'
        content += "\n\n".join(
            box.replace('class="', 'class="max-w-xl mx-auto ')
            for box in boxes
        )
        content += "\n\n</div>\n"

        return frontmatter + title + content
    
    def _format_default(
        self,
        slide: SlideContent,
        content_types: Optional[List[str]],
        frontmatter: str,
        title: str
    ) -> str:
        boxes = self.formatter.format_bullets_with_boxes(slide.content, content_types)
        
        content = '<div class="mt-8 space-y-6">\n\n'
        content += "\n\n".join(boxes)
        content += "\n\n</div>\n"
        
        return frontmatter + title + content
    
    def convert_lecture_to_slidev(
        self,
        lecture_json: dict,
        image_handler,
        optimizer_agent=None
    ) -> str:
        optimization_metadata_map = {}
        
        if optimizer_agent:
            try:
                optimized_json = optimizer_agent.optimize(lecture_json)
                optimization_results = optimized_json.get("optimization_metadata", [])
                for result in optimization_results:
                    optimization_metadata_map[result["slide_id"]] = result["suggestions"]
            except Exception as e:
                print(f"Optimizer agent error: {e}, continuing without optimization")
        
        from src.rendering.section_dividers import add_section_dividers
        
        all_slides = []
        all_slides_markdown = []
        
        for slide_data in lecture_json.get("slides", []):
            slide = SlideContent(**slide_data)
            optimization_metadata = optimization_metadata_map.get(slide.slide_id)
            
            split_slides = self.splitter.analyze_and_split(slide)
            
            for split_slide in split_slides:
                all_slides.append(split_slide)
                image_path = image_handler.resolve_image_path(split_slide.image) if split_slide.image else None
                
                split_optimization = optimization_metadata_map.get(split_slide.slide_id) or optimization_metadata
                
                slide_md = self.convert_slide_to_markdown(split_slide, image_path, split_optimization)
                all_slides_markdown.append(slide_md)
        
        slides_with_dividers = add_section_dividers(all_slides_markdown, all_slides)
        
        return "\n---\n\n".join(slides_with_dividers)

