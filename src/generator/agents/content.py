from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import json
import re
from src.models.slide import SlideContent
from src.utils.config import config

class ContentAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.3, max_tokens=16000)
        self.model = model
        
        self.MIN_BULLET_POINTS = 2
        self.MAX_BULLET_POINTS = 5
        self.OPTIMAL_BULLET_POINTS = 3
        self.MIN_WORDS_PER_BULLET = 5
        self.MAX_WORDS_PER_BULLET = 20
        self.MIN_SPEAKER_NOTES_SENTENCES = 4
        self.MAX_SPEAKER_NOTES_SENTENCES = 15
    
    def process_lecture(self, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
        slides = [SlideContent(**slide_data) for slide_data in lecture_data.get("slides", [])]
        
        design_ready_slides = []
        
        for idx, slide in enumerate(slides, 1):
            design_slide = self._convert_to_design_ready(slide, idx)
            design_ready_slides.append(design_slide)
        
        lecture_title = lecture_data.get("metadata", {}).get("source_document_id", "Untitled Lecture")
        
        output = {
            "lecture_title": lecture_title,
            "total_slides": len(design_ready_slides),
            "slides": design_ready_slides
        }
        
        return output
    
    def _convert_to_design_ready(self, slide: SlideContent, slide_number: int) -> Dict[str, Any]:
        system_prompt = """You are a presentation design expert who transforms raw slide content into design-ready JSON for professional Slidev presentations.

CRITICAL REQUIREMENTS:


1. LATEX FOR MATH FORMULAS - STRICT CONSISTENCY
   - Convert ALL mathematical expressions to LaTeX format: $...$
   - Use STANDARD variables: $x$, $y$, $\\alpha$, $\\beta$ (NOT Â, α without $)
   - Inline math: $x^2$, $\\sin x$, $\\frac{a}{b}$
   - Display math for important formulas: $$...$$
   - Examples: 
     * WRONG: "sin x", "cosÂ", "α", "tanÂ"
     * CORRECT: "$\\sin x$", "$\\cos x$", "$\\alpha$", "$\\tan x$"
   - In JSON, use single backslash: "\\sin" not "\\\\sin"
   - NEVER use special characters like Â, ô, â in formulas - always use LaTeX
   - BE CONSISTENT: Use same variable throughout (e.g., always $x$ or always $\\alpha$, not mixed)


2. COMPONENT SEPARATION - STRICT TABLE DETECTION
   - CRITICAL: Scan EVERY item in content array for "|" character
   - If ANY item contains "|", it is a TABLE → extract it completely
   - Process:
     Step 1: Find all items with "|" pattern
     Step 2: Combine them into ONE table_content string
     Step 3: Remove ALL those items from text_content
     Step 4: Keep ONLY pure text (no "|") in text_content
   
   WRONG (Table mixed with text):
   {
     "text_content": ["Point 1", "| A | B |\\n|---|---|\\n| 1 | 2 |", "Point 2"],
     "table_content": null
   }
   
   CORRECT (Table separated):
   {
     "text_content": ["Point 1", "Point 2"],
     "table_content": "| A | B |\\n|---|---|\\n| 1 | 2 |"
   }

3. FACT-CHECKING FOR MATH/SCIENCE CONTENT
   - Before finalizing, verify mathematical formulas are correct
   - Check common mistakes:
     * Complementary angles: $\\alpha$ and $\\frac{\\pi}{2} - \\alpha$ (NOT $\\pi - \\alpha$)
     * Supplementary angles: $\\alpha$ and $\\pi - \\alpha$
     * Pythagorean identity: $\\sin^2 x + \\cos^2 x = 1$
   - If unsure, keep original formula from source
   - Don't invent or "fix" formulas unless certain

4. LAYOUT INTENT & HINTS
   - Analyze content and assign appropriate intent:
     * "intro" - Title/opening slide
     * "definition" - Definitions, concepts
     * "definition_with_table" - Definition + table (USE when table present!)
     * "comparison" - Comparing items
     * "formula" - Focus on important formula
     * "example" - Examples, applications
     * "summary" - Summary, conclusion
   
   - Suggest layout_hint based on components:
     * "centered" - Center content
     * "split-left-text" - Text left, visual right
     * "split-right-table" - Text left, table right (USE when table exists!)
     * "full-table" - Table takes most space (USE when table is main content!)
     * "formula-focus" - Large centered formula
     * "standard" - Default layout

5. DENSITY CALCULATION
   - Calculate content density for Layout Agent:
     * Count total words in text_content
     * Count table rows if table exists
     * Assign density:
       - "low": ≤30 words, no table OR simple table (≤3 rows)
       - "medium": 31-60 words OR moderate table (4-6 rows)
       - "high": >60 words OR complex table (>6 rows) OR table + text
   - This helps Layout Agent choose font sizes and spacing

6. CONTENT OPTIMIZATION - AVOID DUPLICATES
   - Remove redundancy between slides
   - If two slides have similar intent/content, differentiate them:
     * One focused on definitions → intent: "definition"
     * Another focused on table/comparison → intent: "definition_with_table", layout: "full-table"
   - Optimize density: 3-4 text points ideal
   - Create short_summary (1 sentence) for each slide
   - Extract highlight_keywords (3-5 key terms)
   - If table exists, mention it in short_summary
   - ENSURE COMPLETENESS:
     * Don't leave formulas incomplete (e.g., "Cung phụ nhau: $\alpha$ và $\frac{\pi}{2} - \alpha$" must have formula, not just title)
     * If listing items, complete all items with their details
     * Don't create placeholder content - fill everything

7. USE SAME LANGUAGE AS SOURCE
   - Preserve Vietnamese/English as in original
   - Don't translate unless necessary
   - Work with ANY language (not just Vietnamese/English)

CRITICAL JSON FORMATTING:
- Use proper JSON escaping
- Newlines in strings: \\n (not actual newlines)
- Backslashes in LaTeX: single backslash in JSON string
- Example table: "| Col1 | Col2 |\\n|---|---|\\n| val1 | val2 |"

Return ONLY valid JSON (no markdown code blocks):
{
  "slide_number": 1,
  "title": "Title with $\\LaTeX$ if needed",
  "intent": "definition_with_table",
  "layout_hint": "split-right-table",
  "density": "medium",
  "short_summary": "One sentence summary mentioning table if present",
  "components": {
    "text_content": ["Point 1 with $\\sin x$", "Point 2", "Point 3"],
    "table_content": "| Col1 | Col2 |\\n|---|---|\\n| val1 | val2 |",
    "highlight_keywords": ["keyword1", "keyword2", "keyword3"]
  },
  "visual_asset": {
    "image_id": "img_xxx",
    "url": null,
    "description": "Brief description of what image shows"
  },
  "speaker_notes": "Detailed notes for presenter"
}

IMPORTANT:
- MUST separate tables from text_content - this is critical!
- If NO table found, set "table_content": null
- If table found, MUST set "table_content" with full table and remove from "text_content"
- If no image, set "visual_asset": null
- Always include short_summary, highlight_keywords, and density
- Fact-check math formulas before finalizing
- Convert ALL math to LaTeX
- Return ONLY the JSON object, no markdown formatting"""

        image_info = None
        if slide.image:
            image_info = {
                "image_id": slide.image.image_id,
                "url": slide.image.url
            }

        user_prompt = f"""Transform this raw slide into design-ready JSON:

Title: {slide.title}
Content: {json.dumps(slide.content, ensure_ascii=False)}
Speaker Notes: {slide.speaker_notes}
Image: {json.dumps(image_info, ensure_ascii=False) if image_info else "None"}

Apply all 5 requirements:
1. Convert math to LaTeX
2. Separate tables from text
3. Assign intent and layout_hint
4. Optimize content density
5. Use same language as source"""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        try:
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
            
            content = content.strip()
            
            design_slide = json.loads(content)
            design_slide["slide_number"] = slide_number
            
            design_slide = self._post_process_table_separation(design_slide)
            
            return design_slide
            
        except json.JSONDecodeError as e:
            print(f"Warning: JSON parse error for slide {slide.slide_id}: {str(e)}")
            print(f"Content preview: {content[:200] if 'content' in locals() else 'N/A'}")
            
            fallback = {
                "slide_number": slide_number,
                "title": slide.title,
                "intent": "standard",
                "layout_hint": "standard",
                "density": "medium",
                "short_summary": slide.title,
                "components": {
                    "text_content": slide.content,
                    "table_content": None,
                    "highlight_keywords": []
                },
                "visual_asset": image_info,
                "speaker_notes": slide.speaker_notes
            }
            return self._post_process_table_separation(fallback)
        except Exception as e:
            print(f"Warning: Failed to convert slide {slide.slide_id}: {str(e)}")
            
            fallback = {
                "slide_number": slide_number,
                "title": slide.title,
                "intent": "standard",
                "layout_hint": "standard",
                "density": "medium",
                "short_summary": slide.title,
                "components": {
                    "text_content": slide.content,
                    "table_content": None,
                    "highlight_keywords": []
                },
                "visual_asset": image_info,
                "speaker_notes": slide.speaker_notes
            }
            return self._post_process_table_separation(fallback)
    
    def _post_process_table_separation(self, slide_data: Dict[str, Any]) -> Dict[str, Any]:
        components = slide_data.get("components", {})
        text_content = components.get("text_content", [])
        table_content = components.get("table_content")
        
        table_items = []
        pure_text_items = []
        
        for item in text_content:
            if isinstance(item, str) and "|" in item:
                table_items.append(item)
            else:
                pure_text_items.append(item)
        
        if table_items:
            if not table_content:
                combined_table = "\n".join(table_items)
                components["table_content"] = combined_table
                components["text_content"] = pure_text_items
                
                if slide_data.get("intent") == "standard" and table_items:
                    slide_data["intent"] = "definition_with_table"
                if slide_data.get("layout_hint") == "standard" and table_items:
                    slide_data["layout_hint"] = "split-right-table" if pure_text_items else "full-table"
                
                total_words = sum(len(item.split()) for item in pure_text_items)
                table_rows = combined_table.count("\n") + 1
                
                if total_words <= 30 and table_rows <= 3:
                    density = "low"
                elif total_words > 60 or table_rows > 6 or (pure_text_items and table_items):
                    density = "high"
                else:
                    density = "medium"
                
                slide_data["density"] = density
        
        return slide_data
    
    def analyze_slide_density(self, slide: SlideContent) -> Dict[str, Any]:
        bullet_count = len(slide.content)
        
        words_per_bullet = [len(bullet.split()) for bullet in slide.content]
        avg_words_per_bullet = sum(words_per_bullet) / bullet_count if bullet_count > 0 else 0
        
        speaker_sentences = len(re.split(r'[.!?]+', slide.speaker_notes))
        
        density_score = 0
        issues = []
        suggestions = []
        
        if bullet_count < self.MIN_BULLET_POINTS:
            issues.append(f"Too few bullet points ({bullet_count})")
            suggestions.append(f"Add more content or merge with another slide")
            density_score -= 20
        elif bullet_count > self.MAX_BULLET_POINTS:
            issues.append(f"Too many bullet points ({bullet_count})")
            suggestions.append(f"Split into multiple slides or condense content")
            density_score -= 15
        else:
            density_score += 30
        
        if avg_words_per_bullet < self.MIN_WORDS_PER_BULLET:
            issues.append(f"Bullet points too short (avg {avg_words_per_bullet:.1f} words)")
            suggestions.append("Expand bullet points with more detail")
            density_score -= 15
        elif avg_words_per_bullet > self.MAX_WORDS_PER_BULLET:
            issues.append(f"Bullet points too long (avg {avg_words_per_bullet:.1f} words)")
            suggestions.append("Condense bullet points to key ideas")
            density_score -= 10
        else:
            density_score += 40
        
        if speaker_sentences < self.MIN_SPEAKER_NOTES_SENTENCES:
            issues.append(f"Speaker notes too brief ({speaker_sentences} sentences)")
            suggestions.append("Expand speaker notes with more context and examples")
            density_score -= 10
        elif speaker_sentences > self.MAX_SPEAKER_NOTES_SENTENCES:
            issues.append(f"Speaker notes too verbose ({speaker_sentences} sentences)")
            suggestions.append("Condense speaker notes to essential information")
            density_score -= 5
        else:
            density_score += 30
        
        density_score = max(0, min(100, density_score + 50))
        
        return {
            "slide_id": slide.slide_id,
            "bullet_count": bullet_count,
            "avg_words_per_bullet": avg_words_per_bullet,
            "speaker_sentences": speaker_sentences,
            "density_score": density_score,
            "issues": issues,
            "suggestions": suggestions,
            "needs_optimization": density_score < 70
        }