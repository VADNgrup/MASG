from typing import List, Optional
from src.rendering.style_profile import get_block_style


def detect_content_type(text: str) -> str:
    text_lower = text.lower()

    if any(keyword in text_lower for keyword in ["khái niệm", "định nghĩa", "là gì", "concept", "definition"]):
        return "key_concept"

    if any(keyword in text_lower for keyword in ["công thức", "formula", "equation"]):
        return "formula"

    if any(keyword in text_lower for keyword in ["ví dụ", "example", "minh họa"]):
        return "example"

    if any(keyword in text_lower for keyword in ["tính chất", "property", "đặc điểm"]):
        return "property"

    if any(keyword in text_lower for keyword in ["quan trọng", "important", "lưu ý", "chú ý", "warning"]):
        return "important"

    if any(keyword in text_lower for keyword in ["ghi chú", "note"]):
        return "note"

    return "other"

class ContentFormatter:
    def format_bullets_with_boxes(
        self, 
        bullets: List[str], 
        content_types: Optional[List[str]] = None
    ) -> List[str]:
        if not bullets:
            return []
        
        formatted_boxes = []
        
        for i, bullet in enumerate(bullets):
            content_type = content_types[i] if content_types and i < len(content_types) else None
            if not content_type:
                content_type = detect_content_type(bullet)
            
            box = self._create_gradient_box(bullet, content_type, i + 1)
            formatted_boxes.append(box)
        
        return formatted_boxes
    
    def _create_gradient_box(self, content: str, content_type: str, vclick_num: int) -> str:
        style = get_block_style(content_type)

        box = f'''<div v-click="{vclick_num}" class="{style.surface}">
  <div class="{style.label_class}">
    {style.label_text}
  </div>
  <div class="{style.body_class}">
    {content}
  </div>
</div>'''

        return box
    
    def format_for_two_cols(
        self,
        bullets: List[str],
        content_types: Optional[List[str]] = None,
        split_point: Optional[int] = None
    ) -> tuple[List[str], List[str]]:
        if not split_point:
            split_point = len(bullets) // 2
        
        left_bullets = bullets[:split_point]
        right_bullets = bullets[split_point:]
        
        left_types = content_types[:split_point] if content_types else None
        right_types = content_types[split_point:] if content_types else None
        
        left_boxes = self.format_bullets_with_boxes(left_bullets, left_types)
        right_boxes = self.format_bullets_with_boxes(right_bullets, right_types)
        
        vclick_offset = len(left_boxes)
        right_boxes_adjusted = []
        for i, box in enumerate(right_boxes):
            adjusted_box = box.replace(f'v-click="{i + 1}"', f'v-click="{i + 1 + vclick_offset}"')
            right_boxes_adjusted.append(adjusted_box)
        
        return left_boxes, right_boxes_adjusted

