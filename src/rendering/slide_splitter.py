from typing import List, Dict, Any
from src.models.slide import SlideContent
import copy

def smart_split_slide(slide: SlideContent, optimization_metadata: Dict[str, Any] = None) -> List[SlideContent]:
    if optimization_metadata and optimization_metadata.get("should_split"):
        split_into = optimization_metadata.get("split_into", 2)
        return split_according_to_suggestions(slide, split_into)
    
    if len(slide.content) <= 4:
        return [slide]
    
    chunks = split_into_chunks(slide.content, max_per_chunk=4)
    split_slides = []
    
    for i, chunk in enumerate(chunks):
        new_slide = copy.deepcopy(slide)
        new_slide.content = chunk
        if len(chunks) > 1:
            new_slide.slide_id = f"{slide.slide_id}_part{i+1}"
            new_slide.title = f"{slide.title} (Phần {i+1})"
        split_slides.append(new_slide)
    
    return split_slides

def split_according_to_suggestions(slide: SlideContent, split_into: int) -> List[SlideContent]:
    content_count = len(slide.content)
    items_per_chunk = (content_count + split_into - 1) // split_into
    
    chunks = []
    for i in range(0, content_count, items_per_chunk):
        chunk = slide.content[i:i + items_per_chunk]
        chunks.append(chunk)
    
    split_slides = []
    for i, chunk in enumerate(chunks):
        new_slide = copy.deepcopy(slide)
        new_slide.content = chunk
        new_slide.slide_id = f"{slide.slide_id}_part{i+1}"
        if len(chunks) > 1:
            new_slide.title = f"{slide.title} (Phần {i+1})"
        split_slides.append(new_slide)
    
    return split_slides

def split_into_chunks(content: List[str], max_per_chunk: int = 4) -> List[List[str]]:
    chunks = []
    current_chunk = []
    
    for item in content:
        current_chunk.append(item)
        if len(current_chunk) >= max_per_chunk:
            chunks.append(current_chunk)
            current_chunk = []
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


