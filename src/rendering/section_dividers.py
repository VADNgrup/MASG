from typing import List, Dict, Any
from src.models.slide import SlideContent

def detect_section_changes(slides: List[SlideContent]) -> List[int]:
    section_indices = [0]
    
    for i in range(1, len(slides)):
        prev_title = slides[i-1].title.lower()
        curr_title = slides[i].title.lower()
        
        prev_words = set(prev_title.split()[:3])
        curr_words = set(curr_title.split()[:3])
        
        overlap = len(prev_words & curr_words) / max(len(prev_words | curr_words), 1)
        
        if overlap < 0.3:
            section_indices.append(i)
    
    return section_indices

def generate_section_divider(title: str, subtitle: str = "") -> str:
    if subtitle:
        return f"""---
layout: section
---

# {title}
## {subtitle}

---
"""
    else:
        return f"""---
layout: section
---

# {title}

---
"""

def add_section_dividers(slides_markdown: List[str], slides: List[SlideContent]) -> List[str]:
    if len(slides) < 2:
        return slides_markdown
    
    section_indices = detect_section_changes(slides)
    
    result = []
    last_section_title = None
    
    for i, slide_md in enumerate(slides_markdown):
        if i < len(slides):
            current_title = slides[i].title
            
            if i in section_indices and i > 0:
                if current_title != last_section_title:
                    divider = generate_section_divider(current_title)
                    result.append(divider)
                    last_section_title = current_title
        
        result.append(slide_md)
    
    return result

