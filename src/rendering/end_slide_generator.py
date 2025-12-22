from typing import Optional

def generate_end_slide(lecture_title: str = "Lecture", custom_message: Optional[str] = None) -> str:
    if not custom_message:
        custom_message = "Chúc các bạn học tốt!"
    
    end_content = f"""---
layout: default
class: text-center
---

# Cảm ơn đã theo dõi! 🎓

<div class="mt-8">

<div class="text-6xl mb-4">📚</div>

### {custom_message}
</div>
"""
    
    return end_content

