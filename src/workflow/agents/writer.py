from langchain_openai import ChatOpenAI
from typing import Dict, Optional
import json
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.utils.config import config
from src.optimization.lightning_integration import lightning_integration

class WriterAgent:
    def _extract_relevant_text(self, section: Dict, context: DocumentContext) -> str:
        full_text = context.text_content.markdown
        
        if len(full_text) <= 150000:
            return full_text
        
        section_title = section['title'].lower()
        key_concepts = section.get('key_concepts', [])
        
        if not key_concepts:
            return full_text[:100000]
        
        text_lower = full_text.lower()
        
        best_segments = []
        seen_positions = set()
        
        for keyword in key_concepts:
            keyword_lower = keyword.lower()
            pos = text_lower.find(keyword_lower)
            if pos >= 0:
                start = max(0, pos - 1000)
                end = min(len(full_text), pos + 10000)
                
                segment_key = (start // 5000, end // 5000)
                if segment_key not in seen_positions:
                    seen_positions.add(segment_key)
                    segment = full_text[start:end]
                    best_segments.append(segment)
        
        if best_segments:
            combined = "\n\n---\n\n".join(best_segments[:10])
            if len(combined) >= 50000:
                return combined
            else:
                return combined + "\n\n---\n\n" + full_text[:50000]
        
        return full_text[:100000]
    
    def _fix_incomplete_json(self, json_str: str, original_error: Exception) -> Dict:
        try:
            json_str = json_str.strip()
            
            if json_str.startswith('{{'):
                json_str = json_str[1:]
            
            if not json_str.startswith('{'):
                json_str = '{' + json_str.split('{', 1)[-1] if '{' in json_str else json_str
            
            if '"speaker_notes": "' in json_str:
                last_note_start = json_str.rfind('"speaker_notes": "')
                if last_note_start >= 0:
                    start_note = last_note_start + len('"speaker_notes": "')
                    note_content = json_str[start_note:]
                    note_content = note_content.rstrip().rstrip('"').rstrip(',').rstrip('}')
                    note_content = note_content.replace('\n', ' ').replace('\r', '')
                    note_content = note_content.replace('"', "'")
                    if len(note_content) > 300:
                        note_content = note_content[:300]
                    json_str = json_str[:start_note] + note_content + '"}'
            
            if '"image_query":' not in json_str:
                json_str = json_str.rstrip().rstrip(',').rstrip('}') + ', "image_query": null}'
            
            if not json_str.rstrip().endswith('}'):
                json_str = json_str.rstrip().rstrip(',').rstrip('}') + '}'
            
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as fix_error:
            raise ValueError(f"Failed to parse incomplete JSON. Original: {str(original_error)[:200]}. Fix: {str(fix_error)[:200]}. Content: {json_str[:1000]}") from original_error
    
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
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=8000)
        self.model = model
    
    def draft_slide(
        self, 
        section: Dict, 
        context: DocumentContext, 
        feedback: Optional[str] = None
    ) -> SlideContent:
        text_excerpt = self._extract_relevant_text(section, context)
        
        available_images = self._get_available_images_for_section(section, context)
        
        system_prompt = """You are creating engaging, lively lecture slides that capture the essence and energy of the source material.

CRITICAL: PRESERVE THE ORIGINAL TONE AND STYLE
- Match the energy, enthusiasm, and tone of the source material
- If the source is passionate, be passionate. If it's clear and direct, be clear and direct.
- Don't flatten or sanitize the content - keep its personality!
- Use the same language patterns, expressions, and flow as the source

THINK STEP-BY-STEP:
1. What tone and energy does the source material have? (Enthusiastic? Clear and direct? Detailed? Practical?)
2. What are the 3-5 MOST important points? Preserve their original impact and meaning
3. How did the source present these points? Maintain that style and approach
4. Can one slide cover this? If too much, prioritize the most impactful points

CREATE SLIDES IN THE SAME LANGUAGE AS THE SOURCE MATERIAL WITH:
- Title (max 8 words, capture the essence and energy of the content)
- 3-5 bullet points ONLY (each 8-15 words)
  * PRESERVE the original phrasing and energy when possible
  * Use the same language style as source - if source uses vivid examples, keep them!
  * Don't make it dry or textbook-like - keep it lively and engaging like the original
  * If source uses questions, analogies, or vivid descriptions, preserve those elements
  * Make each point feel natural and compelling, not robotic or formulaic
 - Speaker notes (COMPREHENSIVE and DETAILED explanation, 8-15 sentences):
  * Start immediately with the concept; NEVER include greetings/openings
  * Provide FULL, COMPLETE explanation of all concepts on the slide
  * Match the tone and enthusiasm of the source material
  * Explain with the same energy and clarity as the original
  * Use the same teaching style - if source is detailed, be detailed; if concise, be concise
  * Include the same examples or analogies from source when relevant
  * Expand on each bullet point thoroughly - don't just repeat the bullet points
  * Add context, background, relationships between concepts
  * Explain WHY each point matters and HOW it connects to the bigger picture
  * Include practical applications, real-world connections when relevant
  * Feel natural and engaging, like the original material does
  * Be comprehensive - this is the speaker's full script, not a brief summary
- Image query (in English, specific to this slide's content)

SMART RENDERING METADATA:
Analyze the content and set slide_subtype in metadata field:
- "interactive-math": Trigonometric functions (sin, cos, tan), unit circle, math graphs that can be interactive
- "interactive-code": Code demonstrations that should run live (Python, JavaScript)
- "interactive-chart": Dynamic data visualization, charts, graphs
- "split-view": Minimal text (≤3 points) + 1 important image → display side-by-side
- "standard": Regular text content with adaptive layout

CRITICAL RULES:
1. MAXIMUM 5 bullet points per slide
2. PRESERVE the original tone, energy, and style - don't make it generic or bland
3. Keep the content vibrant and engaging like the source, not dry or mechanical
4. Use the same language patterns and expressions as the source material
5. If source material is detailed and rich, preserve that richness (within the 5-point limit)
6. Use the SAME language as the source material (detect automatically), image_query in English
7. ALWAYS set metadata.slide_subtype based on content analysis

TONE PRESERVATION:
- Read the source material carefully and match its energy
- If it's enthusiastic, be enthusiastic. If it's clear and direct, be clear and direct.
- Preserve vivid language, interesting examples, and engaging explanations
- Don't strip away personality to make it "professional" - keep it alive!

Return ONLY valid JSON:
{{
  "slide_id": "slide_XXX",
  "slide_type": "content",
  "title": "...",
  "content": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"],
  "speaker_notes": "COMPREHENSIVE explanation (8-15 sentences, detailed and thorough) that matches the tone, energy, and style of the source material. Fully explain all concepts, provide context, relationships, examples, and why each point matters. This is the speaker's complete script.",
  "image_query": "specific descriptive query or null",
  "metadata": {{
    "slide_subtype": "interactive-math"
  }}
}}"""
        
        user_prompt = f"""Section: {section['title']}
Key concepts: {', '.join(section['key_concepts'])}
Needs visual: {section.get('needs_visual', False)}

{available_images}

Source material excerpt:
{text_excerpt}

{f"PREVIOUS FEEDBACK TO ADDRESS: {feedback}" if feedback else ""}

Generate ONE slide for this section. Use the SAME language as the source material automatically.
If image needed, create SPECIFIC query matching slide content (not generic "unit circle")."""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
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
                    json_str = json_match.group()
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        data = self._fix_incomplete_json(json_str, e)
                else:
                    raise ValueError(f"No JSON found in LLM response: {content[:500]}") from e
        
        return SlideContent(**data)

