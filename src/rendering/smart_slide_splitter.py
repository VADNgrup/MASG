from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import json
import copy
from src.models.slide import SlideContent

class SmartSlideSplitter:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
    
    def analyze_and_split(self, slide: SlideContent) -> List[SlideContent]:
        content_count = len(slide.content)
        
        if content_count <= 4:
            return [slide]
        
        if content_count > 6:
            return self._llm_based_split(slide)
        
        return [slide]
    
    def _llm_based_split(self, slide: SlideContent) -> List[SlideContent]:
        try:
            bullets_text = "\n".join([f"{i+1}. {bullet}" for i, bullet in enumerate(slide.content)])
            
            prompt = f"""Analyze these bullet points from a slide titled "{slide.title}" and group them semantically.

Bullet points:
{bullets_text}

Task: Group these bullets into 2-3 coherent sub-topics. Each group should have 2-4 bullets maximum.

Rules:
- Group by semantic similarity and topic coherence
- Each group must have at least 2 bullets
- Maximum 4 bullets per group
- Preserve original order when possible
- Be generic: work for any domain (not just math/science)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "groups": [
    {{
      "subtitle": "Brief subtitle for this group",
      "bullet_indices": [0, 1, 2]
    }},
    {{
      "subtitle": "Brief subtitle for this group", 
      "bullet_indices": [3, 4, 5]
    }}
  ]
}}"""
            
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
            groups = result.get("groups", [])
            
            if not groups or len(groups) < 2:
                return self._fallback_split(slide)
            
            return self._create_split_slides(slide, groups)
            
        except Exception as e:
            print(f"SmartSlideSplitter LLM error: {e}, using fallback")
            return self._fallback_split(slide)
    
    def _create_split_slides(self, slide: SlideContent, groups: List[Dict]) -> List[SlideContent]:
        split_slides = []
        
        for i, group in enumerate(groups):
            indices = group.get("bullet_indices", [])
            subtitle = group.get("subtitle", "")
            
            if not indices:
                continue
            
            new_slide = copy.deepcopy(slide)
            new_slide.content = [slide.content[idx] for idx in indices if idx < len(slide.content)]
            
            if len(new_slide.content) == 0:
                continue
            
            new_slide.slide_id = f"{slide.slide_id}_part{i+1}"
            
            if subtitle:
                new_slide.title = f"{slide.title}: {subtitle}"
            else:
                new_slide.title = f"{slide.title} (Part {i+1})"
            
            if i == 0 and slide.image:
                new_slide.image = slide.image
            else:
                new_slide.image = None
            
            split_slides.append(new_slide)
        
        return split_slides if split_slides else [slide]
    
    def _fallback_split(self, slide: SlideContent) -> List[SlideContent]:
        content_count = len(slide.content)
        items_per_chunk = 4
        
        split_slides = []
        for i in range(0, content_count, items_per_chunk):
            chunk = slide.content[i:i + items_per_chunk]
            
            new_slide = copy.deepcopy(slide)
            new_slide.content = chunk
            new_slide.slide_id = f"{slide.slide_id}_part{i//items_per_chunk + 1}"
            new_slide.title = f"{slide.title} (Part {i//items_per_chunk + 1})"
            
            if i == 0 and slide.image:
                new_slide.image = slide.image
            else:
                new_slide.image = None
            
            split_slides.append(new_slide)
        
        return split_slides

