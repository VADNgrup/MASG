from typing import Dict, Any, Optional
from datetime import datetime

def generate_cover_slide(lecture_json: dict) -> str:
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
    
    total_slides = metadata.get("total_slides", 0) if isinstance(metadata, dict) else 0
    
    cover_content = f"""---
theme: default
layout: cover
title: "{lecture_title}"
subtitle: "Generated Lecture Slides"
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
---

# {lecture_title}

<div class="pt-12">
{date_str if date_str else "Generated Lecture"}
</div>

---
"""
    
    return cover_content

