from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json

class IntroSlideGenerator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
        self.section_colors = [
            {"gradient": "from-blue-50 to-blue-100", "emoji": "📐"},
            {"gradient": "from-purple-50 to-purple-100", "emoji": "📏"},
            {"gradient": "from-green-50 to-green-100", "emoji": "⭕"},
            {"gradient": "from-orange-50 to-orange-100", "emoji": "🔢"}
        ]
    
    def generate(self, lecture_json: dict) -> str:
        slides = lecture_json.get("slides", [])
        if not slides:
            return ""
        
        sections = self._group_into_sections(slides)
        
        return self._build_intro_slide(sections)
    
    def _group_into_sections(self, slides: List[Dict]) -> List[Dict[str, Any]]:
        slides_preview = []
        for i, slide in enumerate(slides[:10]):
            title = slide.get("title", "")
            slides_preview.append(f"{i+1}. {title}")
        
        preview_text = "\n".join(slides_preview)
        
        prompt = f"""Analyze these lecture slides and group them into 4 main sections.

Slides:
{preview_text}

Task: Create 4 sections that organize these topics logically.

For each section provide:
- title: Short, descriptive title (max 5 words)
- topics: 2-3 key topics in this section

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "sections": [
    {{
      "title": "Section 1 Title",
      "topics": ["Topic A", "Topic B", "Topic C"]
    }},
    {{
      "title": "Section 2 Title",
      "topics": ["Topic D", "Topic E"]
    }},
    {{
      "title": "Section 3 Title",
      "topics": ["Topic F", "Topic G", "Topic H"]
    }},
    {{
      "title": "Section 4 Title",
      "topics": ["Topic I", "Topic J"]
    }}
  ]
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1]
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group()
            
            result = json.loads(content.strip())
            sections = result.get("sections", [])
            
            if len(sections) != 4:
                return self._fallback_sections(slides)
            
            return sections
            
        except Exception as e:
            print(f"IntroSlideGenerator error: {e}, using fallback")
            return self._fallback_sections(slides)
    
    def _fallback_sections(self, slides: List[Dict]) -> List[Dict[str, Any]]:
        total = len(slides)
        chunk_size = (total + 3) // 4
        
        sections = []
        for i in range(4):
            start = i * chunk_size
            end = min(start + chunk_size, total)
            chunk_slides = slides[start:end]
            
            topics = [slide.get("title", "") for slide in chunk_slides[:3]]
            
            sections.append({
                "title": f"Phần {i+1}",
                "topics": topics
            })
        
        return sections
    
    def _build_intro_slide(self, sections: List[Dict[str, Any]]) -> str:
        intro = """---
layout: intro
---

# Nội dung bài học

<div class="grid grid-cols-2 gap-8 mt-12">

"""
        
        for i, section in enumerate(sections[:4]):
            color_config = self.section_colors[i]
            title = section.get("title", f"Phần {i+1}")
            topics = section.get("topics", [])
            
            if not topics:
                topics = [f"Nội dung phần {i+1}"]
            
            topics_html = "\n".join([f"      <li>• {topic}</li>" for topic in topics[:3]])
            
            card = f'''<div v-click="{i+1}" class="flex items-start gap-4 p-6 bg-gradient-to-br {color_config["gradient"]} rounded-2xl transform transition hover:scale-105 hover:shadow-xl">
  <div class="text-4xl">{color_config["emoji"]}</div>
  <div>
    <h3 class="font-bold text-lg mb-2">{title}</h3>
    <ul class="text-sm space-y-1 opacity-80">
{topics_html}
    </ul>
  </div>
</div>

'''
            intro += card
        
        intro += "</div>\n"
        
        return intro

