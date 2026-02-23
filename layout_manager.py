"""
Layout Manager for Slidev Presentation Generation

This module provides a metadata-based approach to select appropriate Slidev layouts
for slides without loading full template files into context. It uses layout descriptors
to intelligently match slide content with the most suitable layout.

Strategy:
1. Define metadata for each layout (capabilities, slots, use cases)
2. Analyze slide data structure (content, images, tables)
3. Select the best matching layout based on content characteristics
"""
import json
import os
import shutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from src.workflow.agents.writer import WriterAgent

class LayoutType(Enum):
    """Available Slidev layout types"""
    STANDARD = "Standard"
    SPLIT = "split"
    SPLIT_2_RIGHT_COMPONENT = "split-2-right-component"
    ONLY_COMPONENT = "only_component"


@dataclass
class LayoutMetadata:
    """Metadata describing a layout's capabilities and structure"""
    name: str
    layout_type: LayoutType
    description: str
    slots: List[str]
    use_cases: List[str]
    max_components: int
    supports_split_view: bool
    supports_caption: bool
    best_for_content_heavy: bool
    best_for_visual_heavy: bool


class LayoutRegistry:
    """Registry of all available layouts with their metadata"""
    
    LAYOUTS = {
        LayoutType.STANDARD: LayoutMetadata(
            name="Standard",
            layout_type=LayoutType.STANDARD,
            description="Basic layout for text-only slides with bullet points",
            slots=["default"],
            use_cases=[
                "Text-only content",
                "Bullet points without images",
                "Introduction or conclusion slides",
                "Slides with only speaker notes"
            ],
            max_components=0,
            supports_split_view=False,
            supports_caption=False,
            best_for_content_heavy=True,
            best_for_visual_heavy=False
        ),
        
        LayoutType.SPLIT: LayoutMetadata(
            name="Split",
            layout_type=LayoutType.SPLIT,
            description="Two-column layout with content on left and single image/component on right",
            slots=["title", "left", "right", "right-caption"],
            use_cases=[
                "Bullet points with one image",
                "Text explanation with visual support",
                "Single chart or diagram with description",
                "Content with one visual element"
            ],
            max_components=1,
            supports_split_view=True,
            supports_caption=True,
            best_for_content_heavy=True,
            best_for_visual_heavy=False
        ),
        
        LayoutType.SPLIT_2_RIGHT_COMPONENT: LayoutMetadata(
            name="Split with 2 Right Components",
            layout_type=LayoutType.SPLIT_2_RIGHT_COMPONENT,
            description="Two-column layout with content on left and two stacked components on right",
            slots=["title", "left", "right-top", "right-top-caption", "right-bottom", "right-bottom-caption"],
            use_cases=[
                "Bullet points with two images",
                "Text with two charts/tables",
                "Comparison of two visuals",
                "Before/after visualizations"
            ],
            max_components=2,
            supports_split_view=True,
            supports_caption=True,
            best_for_content_heavy=False,
            best_for_visual_heavy=True
        ),
        
        LayoutType.ONLY_COMPONENT: LayoutMetadata(
            name="Only Component",
            layout_type=LayoutType.ONLY_COMPONENT,
            description="Layout focused on a single large component (image, table, or chart) with caption",
            slots=["title", "component", "caption"],
            use_cases=[
                "Large table display",
                "Important diagram or architecture",
                "Key chart or graph",
                "Visual-first slides with minimal text"
            ],
            max_components=1,
            supports_split_view=False,
            supports_caption=True,
            best_for_content_heavy=False,
            best_for_visual_heavy=True
        )
    }
    
    @classmethod
    def get_layout(cls, layout_type: LayoutType) -> LayoutMetadata:
        """Get layout metadata by type"""
        return cls.LAYOUTS[layout_type]
    
    @classmethod
    def get_all_layouts(cls) -> Dict[LayoutType, LayoutMetadata]:
        """Get all available layouts"""
        return cls.LAYOUTS


class LayoutSelector:
    """Intelligent layout selector based on slide content analysis"""
    
    def __init__(self, document_id: str):
        self.registry = LayoutRegistry()
        self.document_id = document_id
    
    def analyze_slide(self, slide_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze slide data to extract content characteristics
        
        Args:
            slide_data: Slide data from JSON (e.g., from lec_607fe87f.json)
        
        Returns:
            Dictionary with content analysis
        """
        analysis = {
            "has_content": bool(slide_data.get("content")),
            "content_count": len(slide_data.get("content", [])),
            "has_image": slide_data.get("image") is not None,
            "has_table": slide_data.get("slide_table") is not None,
            "is_chart": False,
            "component_count": 0,
            "slide_subtype": slide_data.get("metadata", {}).get("slide_subtype", "standard")
        }
        
        # Check if image is actually a chart
        if analysis["has_image"]:
            image_metadata = slide_data["image"].get("metadata", {})
            analysis["is_chart"] = image_metadata.get("is_chart", False)
        
        # Count visual components
        if analysis["has_image"]:
            analysis["component_count"] += 1
        if analysis["has_table"]:
            analysis["component_count"] += 1
        
        return analysis
    
    def select_layout(self, slide_data: Dict[str, Any]) -> LayoutType:
        """
        Select the most appropriate layout for a slide
        
        Args:
            slide_data: Slide data from JSON
        
        Returns:
            Selected LayoutType
        """
        analysis = self.analyze_slide(slide_data)
        
        # Decision tree for layout selection
        
        # Case 1: No visual components - use Standard layout
        if analysis["component_count"] == 0:
            return LayoutType.STANDARD
        
        # Case 2: Has table but no other content - use only_component for table focus
        if analysis["has_table"] and analysis["content_count"] <= 2:
            return LayoutType.ONLY_COMPONENT
        
        # Case 3: Has chart and minimal content - use only_component for chart focus
        if analysis["is_chart"] and analysis["content_count"] <= 3:
            return LayoutType.ONLY_COMPONENT
        
        # Case 4: Multiple components - use split-2-right-component
        if analysis["component_count"] >= 2:
            return LayoutType.SPLIT_2_RIGHT_COMPONENT
        
        # Case 5: Single component with content - use split layout
        if analysis["component_count"] == 1 and analysis["has_content"]:
            return LayoutType.SPLIT
        
        # Case 6: Single large image/component - use only_component
        if analysis["component_count"] == 1 and not analysis["has_content"]:
            return LayoutType.ONLY_COMPONENT
        
        # Default: Standard layout
        return LayoutType.STANDARD
    
    def get_layout_info(self, layout_type: LayoutType) -> LayoutMetadata:
        """Get detailed information about a layout"""
        return self.registry.get_layout(layout_type)
    
    def generate_slide_markdown(self, slide_data: Dict[str, Any], layout_type: Optional[LayoutType] = None) -> str:
        """
        Generate Slidev markdown for a slide with the appropriate layout
        
        Args:
            slide_data: Slide data from JSON
            layout_type: Optional specific layout to use (auto-select if None)
        
        Returns:
            Markdown string for the slide
        """
        if layout_type is None:
            layout_type = self.select_layout(slide_data)
        
        layout_meta = self.get_layout_info(layout_type)
        analysis = self.analyze_slide(slide_data)
        
        # Start building markdown
        lines = []
        
        # Add layout declaration (skip for Standard which is default)
        if layout_type != LayoutType.STANDARD:
            lines.append("---")
            lines.append(f"layout: {layout_type.value}")
            lines.append("---")
            lines.append("")
        else:
            lines.append("---")
            lines.append("")
        
        # Generate content based on layout type
        if layout_type == LayoutType.STANDARD:
            lines.extend(self._generate_standard_content(slide_data))
        
        elif layout_type == LayoutType.SPLIT:
            lines.extend(self._generate_split_content(slide_data))
        
        elif layout_type == LayoutType.SPLIT_2_RIGHT_COMPONENT:
            lines.extend(self._generate_split_2_content(slide_data))
        
        elif layout_type == LayoutType.ONLY_COMPONENT:
            lines.extend(self._generate_only_component_content(slide_data))
        
        return "\n".join(lines)
    
    def _generate_standard_content(self, slide_data: Dict[str, Any]) -> List[str]:
        """Generate content for Standard layout"""
        lines = []
        lines.append(f"# {slide_data.get('slide_title', 'Untitled')}")
        
        for bullet in slide_data.get("content", []):
            lines.append(f"- {bullet}")
        
        return lines
    
    def _generate_split_content(self, slide_data: Dict[str, Any]) -> List[str]:
        """Generate content for Split layout"""
        lines = []
        
        # Title slot
        lines.append("::title::")
        lines.append(f"# {slide_data.get('slide_title', 'Untitled')}")
        
        # Left slot (content)
        lines.append("::left::")
        for bullet in slide_data.get("content", []):
            lines.append(f"- {bullet}")
        
        # Right slot (image/component)
        lines.append("::right::")
        if slide_data.get("image"):
            web_path = slide_data["image"].get("path", "")
            lines.append(f'<img src="{web_path}" class="max-h-60 mx-auto"/>')
        
        # Caption slot
        if slide_data.get("image"):
            lines.append("::right-caption::")
            # You can add caption logic here if available in slide_data
            lines.append("Image caption")
        
        return lines
    
    def _generate_split_2_content(self, slide_data: Dict[str, Any]) -> List[str]:
        """Generate content for Split-2-Right-Component layout"""
        lines = []
        
        # Title slot
        lines.append("::title::")
        lines.append(f"# {slide_data.get('slide_title', 'Untitled')}")
        lines.append("")
        
        # Left slot (content)
        lines.append("::left::")
        for bullet in slide_data.get("content", []):
            lines.append(f"- {bullet}")
        lines.append("")
        
        # Right top slot
        lines.append("::right-top::")
        if slide_data.get("image"):
            web_path = slide_data["image"].get("path", "")
            lines.append(f'<img src="{web_path}" class="max-h-60 mx-auto"/>')
        
        lines.append("::right-top-caption::")
        lines.append("Top component caption")
        
        # Right bottom slot
        lines.append("::right-bottom::")
        if slide_data.get("slide_table"):
            # Render table markdown
            lines.append(slide_data["slide_table"].get("table_markdown", ""))
        
        lines.append("")
        lines.append("::right-bottom-caption::")
        lines.append("Bottom component caption")
        
        return lines
    
    def _generate_only_component_content(self, slide_data: Dict[str, Any]) -> List[str]:
        """Generate content for Only-Component layout"""
        lines = []
        
        # Title slot
        lines.append("::title::")
        lines.append(f"# {slide_data.get('slide_title', 'Untitled')}")
        
        # Component slot
        lines.append("::component::")
        
        # Prioritize table over image for this layout
        if slide_data.get("slide_table"):
            lines.append(slide_data["slide_table"].get("table_markdown", ""))
        elif slide_data.get("image"):
            web_path = slide_data["image"].get("path", "")
            lines.append(f'<img src="{web_path}" class="max-h-60 mx-auto"/>')
        
        # Caption slot
        lines.append("::caption::")
        lines.append("Component caption")
        
        return lines


# Convenience functions
def select_layout_for_slide(slide_data: Dict[str, Any]) -> LayoutType:
    """
    Quick function to select layout for a slide
    
    Args:
        slide_data: Slide data dictionary
    
    Returns:
        Selected LayoutType
    """
    selector = LayoutSelector()
    return selector.select_layout(slide_data)


def generate_slide(slide_data: Dict[str, Any], layout_type: Optional[LayoutType] = None) -> str:
    """
    Quick function to generate slide markdown
    
    Args:
        slide_data: Slide data dictionary
        layout_type: Optional specific layout (auto-select if None)
    
    Returns:
        Markdown string for the slide
    """
    selector = LayoutSelector()
    return selector.generate_slide_markdown(slide_data, layout_type)


def get_layout_description(layout_type: LayoutType) -> str:
    """
    Get human-readable description of a layout
    
    Args:
        layout_type: Layout type to describe
    
    Returns:
        Description string
    """
    meta = LayoutRegistry.get_layout(layout_type)
    return f"{meta.name}: {meta.description}"

def generate_toc_slide(outline_path: str) -> str:
    """
    Generate a table of contents slide from outline markdown file
    
    Args:
        outline_path: Path to the outline markdown file
    
    Returns:
        Markdown string for the TOC slide
    """
    try:
        with open(outline_path, "r", encoding="utf-8") as f:
            outline_md = f.read()
        
        # Convert outline to numbered format
        _, numbered_md = WriterAgent.outline_md_to_number(outline_md)
        
        # Create TOC slide
        lines = [
            "---",
            "",
            "# 📋 Table of Contents",
            "",
        ]
        
        # Add numbered outline items
        for line in numbered_md.split("\n"):
            if line.strip():
                lines.append(f"- {line}")
        
        return "\n".join(lines)
    
    except FileNotFoundError:
        print(f"Warning: Outline file not found: {outline_path}")
        return ""

def generate_all_slides(lecture_path, slide_save_name, title = "No Titile", speaker = "No Speaker"):
    # Load main lecture content
    with open(lecture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract base path and lecture_id from lecture_path
    # e.g., "data/lectures/lec_607fe87f.json" -> "data/lectures/lec_607fe87f"
    base_path = lecture_path.rsplit(".", 1)[0]
    
    # Load table distribution file
    table_distribution_path = f"{base_path}_table_distribution.json"
    table_distribution = []
    try:
        with open(table_distribution_path, "r", encoding="utf-8") as f:
            table_distribution = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Table distribution file not found: {table_distribution_path}")
    
    # Load image distribution file
    image_distribution_path = f"{base_path}_image_distributions.json"
    image_distribution = []
    try:
        with open(image_distribution_path, "r", encoding="utf-8") as f:
            image_distribution = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Image distribution file not found: {image_distribution_path}")
    
    # Create lookup dictionaries for tables and images by slide_number
    tables_by_slide = {item["slide_number"]: item for item in table_distribution}
    images_by_slide = {item["slide_number"]: item for item in image_distribution}
    
    # Merge data into slides
    slides = data["slides"]
    for slide in slides:
        slide_num = slide["slide_number"]
        
        # Add table data if exists for this slide
        if slide_num in tables_by_slide:
            table_info = tables_by_slide[slide_num]
            slide["slide_table"] = {
                "table_markdown": table_info.get("table_data", ""),
                "caption": table_info.get("table_caption", ""),
                "chart_path": table_info.get("chart_path", ""),
                "relevance_score": table_info.get("relevance_score", 0)
            }
        
        # Add image data if exists for this slide
        if slide_num in images_by_slide:
            image_info = images_by_slide[slide_num]
            slide["image"] = {
                "path": image_info.get("image_path", ""),
                "clip_score": image_info.get("clip_score", 0),
                "source": image_info.get("source", ""),
                "metadata": {
                    "is_chart": "chart" in image_info.get("image_path", "").lower()
                }
            }
    
    
    document_id = data["metadata"]["source_document_id"]
    
    # Create assets directory if it doesn't exist
    assets_dir = "D:/python/LecSlideGen/slidev/public/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # Copy images and charts to assets directory and update paths
    for slide in slides:
        slide_num = slide["slide_number"]
        
        # Copy and update image path
        if "image" in slide and slide["image"].get("path"):
            original_path = slide["image"]["path"]
            # Normalize path separators
            original_path = original_path.replace("\\", "/")
            
            if os.path.exists(original_path):
                # Get filename from path
                filename = os.path.basename(original_path)
                # Create unique filename to avoid conflicts
                new_filename = f"slide_{slide_num}_{filename}"
                dest_path = os.path.join(assets_dir, new_filename)
                
                # Copy file
                shutil.copy2(original_path, dest_path)
                print(f"Copied image: {original_path} -> {dest_path}")
                
                # Update path in slide data to web path
                slide["image"]["path"] = f"/assets/{new_filename}"
            else:
                print(f"Warning: Image file not found: {original_path}")
        
        # Copy and update chart path
        if "slide_table" in slide and slide["slide_table"].get("chart_path"):
            original_path = slide["slide_table"]["chart_path"]
            # Normalize path separators
            original_path = original_path.replace("\\", "/")
            
            if os.path.exists(original_path):
                # Get filename from path
                filename = os.path.basename(original_path)
                # Create unique filename to avoid conflicts
                new_filename = f"slide_{slide_num}_chart_{filename}"
                dest_path = os.path.join(assets_dir, new_filename)
                
                # Copy file
                shutil.copy2(original_path, dest_path)
                print(f"Copied chart: {original_path} -> {dest_path}")
                
                # Update path in slide data to web path
                slide["slide_table"]["chart_path"] = f"/assets/{new_filename}"
            else:
                print(f"Warning: Chart file not found: {original_path}")
    
    selector = LayoutSelector(document_id)
    config = "---\ntheme: seriph\ntitle: Demo Slidev\ninfo: Slide\nkatex: true"
    front_slide = "\n---\n\n# 👋 Presentation about {title}\nSpeaker: {speaker}\n\n"
    
    # Generate TOC slide from outline file
    outline_path = f"{base_path}_outline.md"
    toc_slide = generate_toc_slide(outline_path)
    
    end_slide = "\n---\n layout: center\nclass: text-center\n---\n\n# Thank You!\n----\n"
    content_slide = ""
    for slide in slides:
        # Analyze and select layout
        analysis = selector.analyze_slide(slide)
        print("Slide Analysis:", analysis)
        
        selected_layout = selector.select_layout(slide)
        print(f"\nSelected Layout: {selected_layout.value}")
    
        layout_info = selector.get_layout_info(selected_layout)
        print(f"Layout Description: {layout_info.description}")
        print(f"Slots: {layout_info.slots}")
    
        # Generate markdown
        markdown = selector.generate_slide_markdown(slide)
        content_slide = content_slide + markdown + "\n"
    
    # Combine all slides: config + front + TOC + content + end
    full_slide_markdown = config + front_slide + toc_slide + "\n" + content_slide + end_slide
    with open(f"D:/python/LecSlideGen/slidev/{slide_save_name}.md", "w", encoding="utf-8") as f:
        f.write(full_slide_markdown)
# Example usage
if __name__ == "__main__":
    generate_all_slides("D:/python/LecSlideGen/data/lectures/lec_b481e59e.json", "test_1", "Sinh Học 10 Bài 14", "Nguyen Khac An")

        
