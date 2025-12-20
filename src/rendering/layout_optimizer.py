from typing import Optional, Dict, Any
from src.models.slide import SlideContent

def determine_optimal_layout(
    slide: SlideContent, 
    image_path: Optional[str] = None, 
    optimization_metadata: Dict[str, Any] = None
) -> str:
    if optimization_metadata and optimization_metadata.get("suggested_layout"):
        return optimization_metadata["suggested_layout"]
    
    has_image = image_path is not None
    content_length = len(slide.content)
    
    if not has_image:
        return "centered" if content_length <= 3 else "default"
    
    if slide.image and slide.image.metadata.get("content_type") in ["table_image", "diagram"]:
        return "image-bottom"
    
    if content_length <= 4:
        return "two-cols"
    else:
        return "image-bottom"


