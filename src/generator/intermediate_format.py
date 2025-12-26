from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class SlideType(Enum):
    INTRO = "intro"
    CONTENT_HEAVY = "content_heavy"
    VISUAL_FOCUS = "visual_focus"
    COMPARISON = "comparison"
    STATEMENT = "statement"
    CONCLUSION = "conclusion"

class ContentDensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class IntermediateSlide:
    title: str
    content: List[str]
    slide_type: str
    
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    
    analyzed_type: Optional[SlideType] = None
    content_density: Optional[ContentDensity] = None
    text_length: int = 0
    bullet_count: int = 0
    has_image: bool = False
    
    suggested_layouts: List[str] = field(default_factory=list)
    selected_layout: Optional[str] = None
    
    theme: Dict[str, Any] = field(default_factory=dict)
    
    animations: Dict[str, Any] = field(default_factory=dict)
    
    decorations: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.text_length = sum(len(c) for c in self.content)
        self.bullet_count = len(self.content)
        self.has_image = bool(self.image_id or self.image_url)

def transform_to_intermediate(raw_slides: List[Dict]) -> List[IntermediateSlide]:
    intermediate_slides = []
    
    for i, slide in enumerate(raw_slides):
        image_id = None
        image_url = None
        
        image_data = slide.get("image")
        if isinstance(image_data, dict):
            image_id = image_data.get("image_id")
            if image_id:
                image_id = f"/assets/{image_id}.png"
            else:
                image_url = image_data.get("url")
        elif isinstance(image_data, str):
            image_url = image_data
        
        content = slide.get("content", [])
        if isinstance(content, str):
            content = [content]
        
        intermediate = IntermediateSlide(
            title=slide.get("title", ""),
            content=content,
            slide_type=slide.get("slide_type", "content"),
            image_id=image_id,
            image_url=image_url,
            metadata={"original_index": i}
        )
        
        intermediate_slides.append(intermediate)
    
    return intermediate_slides
