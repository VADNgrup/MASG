from langchain_openai import ChatOpenAI
from typing import Dict, Optional
import json
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.utils.config import config

class WriterAgent:
    def _detect_language(self, text: str) -> str:
        vietnamese_chars = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư', 'á', 'à', 'ả', 'ã', 'ạ']
        text_lower = text[:500].lower()
        
        for char in vietnamese_chars:
            if char in text_lower:
                return "Vietnamese"
        
        return "English"
    
    def _extract_relevant_text(self, section: Dict, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        section_title = section['title'].lower()
        key_concepts = section.get('key_concepts', [])
        
        text_lower = full_text.lower()
        
        best_segments = []
        for keyword in key_concepts:
            keyword_lower = keyword.lower()
            pos = text_lower.find(keyword_lower)
            if pos >= 0:
                start = max(0, pos - 300)
                end = min(len(full_text), pos + 2000)
                segment = full_text[start:end]
                best_segments.append(segment)
        
        if best_segments:
            combined = "\n\n---\n\n".join(best_segments[:3])
            return combined
        
        return full_text[:5000]
    
    def _get_available_images_for_section(self, section: Dict, context: DocumentContext) -> str:
        relevant_images = []
        
        for img in context.assets.images:
            if img.is_decoration:
                continue
            
            if img.content_type in ["diagram", "table_image", "technical_diagram"]:
                caption_preview = img.caption_display[:150] if img.caption_display else img.caption_rag[:150]
                relevant_images.append(f"- {img.image_id}: {img.content_type} - {caption_preview}")
        
        if relevant_images:
            return f"\nAvailable images from document:\n" + "\n".join(relevant_images[:5])
        return ""
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.4)
    
    def draft_slide(
        self, 
        section: Dict, 
        context: DocumentContext, 
        feedback: Optional[str] = None
    ) -> SlideContent:
        text_excerpt = self._extract_relevant_text(section, context)
        
        language = self._detect_language(text_excerpt)
        
        available_images = self._get_available_images_for_section(section, context)
        
        system_prompt = f"""You are an expert educational content writer creating comprehensive lecture slides.

THINK STEP-BY-STEP:
1. What are ALL the key points in the source material for this section?
2. Which information is essential for understanding? (Include ALL of it)
3. How can I organize this into clear, detailed bullet points?
4. What context and explanations does the speaker need?

CREATE SLIDES IN {language.upper()} LANGUAGE WITH:
- Title (max 8 words, specific to content)
- 6-8 bullet points (each 10-20 words, detailed and specific)
  * Include definitions, formulas, properties, examples
  * Do NOT summarize - include complete information
  * Each point should be self-contained and clear
- Speaker notes (5-7 sentences explaining):
  * What the concept is
  * Why it matters
  * How it relates to other concepts
  * Examples or applications
  * Common misconceptions to clarify
- Image query (in English, specific to this slide's content)

CRITICAL RULES:
1. Extract ALL information from source - do not skip or summarize
2. Be COMPREHENSIVE not concise
3. Speaker notes must provide deep explanation
4. Content must be in {language}, image_query in English

Return ONLY valid JSON:
{{
  "slide_id": "slide_XXX",
  "slide_type": "content",
  "title": "...",
  "content": ["Detailed point 1", "Detailed point 2", "...", "Point 6-8"],
  "speaker_notes": "Comprehensive explanation with 5-7 sentences covering definition, importance, relationships, examples, and clarifications.",
  "image_query": "specific descriptive query or null"
}}"""
        
        user_prompt = f"""Section: {section['title']}
Key concepts: {', '.join(section['key_concepts'])}
Needs visual: {section.get('needs_visual', False)}

{available_images}

Source material excerpt (in {language}):
{text_excerpt}

{f"PREVIOUS FEEDBACK TO ADDRESS: {feedback}" if feedback else ""}

Generate ONE slide for this section. Remember: ALL content must be in {language}!
If image needed, create SPECIFIC query matching slide content (not generic "unit circle")."""
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content.strip()
            
            if "```json" in content:
                parts = content.split("```json")
                if len(parts) > 1:
                    content = parts[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1]
            
            content = content.strip()
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                    except:
                        raise ValueError(f"Failed to parse JSON from LLM response: {content[:500]}") from e
                else:
                    raise ValueError(f"No JSON found in LLM response: {content[:500]}") from e
        
        return SlideContent(**data)

