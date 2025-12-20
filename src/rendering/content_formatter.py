from typing import List, Optional, Dict, Any
import re

def format_bullet_with_style(bullet: str, content_type: Optional[str] = None) -> str:
    if not content_type:
        content_type = detect_content_type(bullet)
    
    if content_type == "formula":
        return f'<span style="color: #6366f1; font-weight: 500">{bullet}</span>'
    elif content_type == "definition":
        return f'<span style="color: #2563eb">{bullet}</span>'
    elif content_type == "example":
        return f'<span style="color: #059669">{bullet}</span>'
    elif content_type == "property":
        return f'<span style="color: #ea580c">{bullet}</span>'
    else:
        return bullet

def detect_content_type(bullet: str) -> str:
    bullet_lower = bullet.lower()
    
    if any(char in bullet for char in ["=", "≤", "≥", "∈", "π", "sin", "cos", "tan", "cot", "+", "-", "×", "÷"]):
        if re.search(r'[a-zA-Z]\s*[=≤≥]\s*', bullet) or re.search(r'\d+\s*[=≤≥]\s*', bullet):
            return "formula"
    
    if bullet.startswith("Tập") or bullet.startswith("Điều kiện") or "là" in bullet[:30]:
        return "definition"
    
    if "Ví dụ" in bullet or "Example" in bullet or "ví dụ" in bullet_lower:
        return "example"
    
    if "có" in bullet_lower[:20] or "là" in bullet_lower[:20]:
        return "property"
    
    return "other"

def format_slide_content(content: List[str], content_types: Optional[List[str]] = None, visual_hints: Optional[Dict[str, Any]] = None) -> List[str]:
    if not visual_hints or not visual_hints.get("use_icons", True):
        return content
    
    formatted = []
    for i, bullet in enumerate(content):
        content_type = content_types[i] if content_types and i < len(content_types) else None
        formatted_bullet = format_bullet_with_style(bullet, content_type)
        formatted.append(formatted_bullet)
    
    return formatted


