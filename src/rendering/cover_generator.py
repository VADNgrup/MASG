from typing import Dict, Any, Optional
from datetime import datetime

def generate_cover_slide(
    lecture_json: dict, 
    theme: str = "seriph",
    theme_config: Dict[str, Any] = None,
    background_url: str = None
) -> str:
    metadata = lecture_json.get("metadata", {})
    
    lecture_title = "Lecture Slides"
    if isinstance(metadata, dict):
        lecture_title = metadata.get("title", "Lecture Slides")
    
    if not lecture_title or lecture_title == "Lecture":
        lecture_title = "Lecture Slides"
    
    generated_at = metadata.get("generated_at", "") if isinstance(metadata, dict) else ""
    date_str = ""
    if generated_at:
        try:
            if "T" in generated_at:
                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(generated_at)
            date_str = dt.strftime("%d/%m/%Y")
        except:
            date_str = generated_at[:10] if len(generated_at) >= 10 else ""
    
    if not background_url:
        background_url = "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1920"
    
    if not theme_config:
        theme_config = {
            "highlighter": "shiki",
            "lineNumbers": False,
            "transition": "slide-left"
        }
    
    highlighter = theme_config.get("highlighter", "shiki")
    line_numbers = "true" if theme_config.get("lineNumbers", False) else "false"
    transition = theme_config.get("transition", "slide-left")
    
    cover_content = f"""---
theme: {theme}
background: {background_url}
class: text-center
highlighter: {highlighter}
lineNumbers: {line_numbers}
info: |
  ## {lecture_title}
  Professional lecture presentation
drawings:
  persist: false
transition: {transition}
title: {lecture_title}
mdc: true
fonts:
  sans: 'Roboto'
  serif: 'Roboto Slab'
  mono: 'Fira Code'
---

# {lecture_title}

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-6 py-3 rounded-full cursor-pointer bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold hover:scale-110 transition-transform inline-block">
    Bắt đầu học ngay <carbon:arrow-right class="inline ml-2"/>
  </span>
</div>

---
"""
    
    return cover_content

