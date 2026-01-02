from langchain_openai import ChatOpenAI
from typing import Dict, Optional
import json
from src.models.context import DocumentContext
from src.models.slide import SlideContent
from src.utils.config import config
from src.optimization.lightning_integration import lightning_integration
from src.utils.latex_processor import process_slide_latex

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
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
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

CRITICAL: PRESERVE THE ORIGINAL TONE, STYLE, AND CONTENT STRUCTURE
- Match the energy, enthusiasm, and tone of the source material
- If the source is passionate, be passionate. If it's clear and direct, be clear and direct.
- Don't flatten or sanitize the content - keep its personality!
- Use the same language patterns, expressions, and flow as the source
- PRESERVE ALL ORIGINAL CONTENT STRUCTURES: tables, code blocks, diagrams, lists, and formatting
- When source material contains tables, maintain them in complete markdown format
- Keep technical content, formulas, code snippets, and structured data intact

MATHEMATICAL FORMULAS - CRITICAL LATEX RULES:
- ALL mathematical expressions MUST be wrapped in LaTeX delimiters
- Use $...$ for inline math: "The formula $\\sin^2 x + \\cos^2 x = 1$ is fundamental"
- Use $$...$$ for block/display math on its own line
- Trigonometric functions MUST use backslash: $\\sin$, $\\cos$, $\\tan$, $\\cot$, NOT sin, cos, tan
- Greek letters MUST use LaTeX: $\\alpha$, $\\beta$, $\\pi$, NOT α, β, π in plain text
- Fractions: $\\frac{a}{b}$ NOT a/b for important formulas
- Superscripts: $x^2$, $\\sin^2 x$ NOT x^2 or sin²x
- Subscripts: $x_1$, $a_n$ NOT x1 or a_n in plain text
- Special symbols: $\\neq$, $\\leq$, $\\geq$, $\\pm$, $\\infty$
- Example CORRECT: "Công thức cơ bản: $\\sin^2 \\alpha + \\cos^2 \\alpha = 1$"
- Example WRONG: "Công thức cơ bản: sin²α + cos²α = 1"

CONTENT PRESERVATION RULES:
- If source has tables in markdown format, preserve them EXACTLY as they appear
- Example: Keep tables like "| Cột 1 | Cột 2 |\n| ----- | ----- |\n| 1 | 2 |" completely intact
- Maintain code blocks, mathematical formulas, and technical diagrams without modification
- Preserve lists, numbering, and hierarchical structures from the original
- Don't summarize or remove structured content - keep it complete and accurate

THINK STEP-BY-STEP:
1. What tone and energy does the source material have? (Enthusiastic? Clear and direct? Detailed? Practical?)
2. What are the 3-5 MOST important points? Preserve their original impact and meaning
3. How did the source present these points? Maintain that style and approach
4. Are there tables, code, or structured content? Keep them complete and unmodified
5. Are there mathematical formulas? Wrap ALL of them in proper LaTeX $...$ or $$...$$
6. Can one slide cover this? If too much, prioritize the most impactful points while keeping structures intact

CREATE SLIDES IN THE SAME LANGUAGE AS THE SOURCE MATERIAL WITH:
- Title (max 8 words, capture the essence and energy of the content)
- Content array with 3-5 items:
  * SPECIAL CASE - TABLES: If source contains markdown tables, include the COMPLETE table as ONE item in content array
    Example: ["| Cột 1 | Cột 2 | Cột 3 |\n| ----- | ----- | ----- |\n| 1 | 2 | 3 |", "Additional context point", "Another point"]
  * SPECIAL CASE - MATH: All formulas MUST be in LaTeX format with $ or $$
    Example: ["Hệ thức cơ bản: $\\sin^2 x + \\cos^2 x = 1$", "Với $\\cos x \\neq 0$: $\\tan x = \\frac{\\sin x}{\\cos x}$"]
  * For regular content: 3-5 bullet points (each 8-15 words)
  * PRESERVE the original phrasing and energy when possible
  * Use the same language style as source - if source uses vivid examples, keep them!
  * Don't make it dry or textbook-like - keep it lively and engaging like the original
  * If source uses questions, analogies, or vivid descriptions, preserve those elements
  * Make each point feel natural and compelling, not robotic or formulaic
  * NEVER summarize tables into text - always include the complete markdown table
 - Speaker notes (COMPREHENSIVE and DETAILED explanation, 8-15 sentences):
  * Start immediately with the concept; NEVER include greetings/openings
  * Provide FULL, COMPLETE explanation of all concepts on the slide
  * Match the tone and enthusiasm of the source material
  * Explain with the same energy and clarity as the original
  * Use the same teaching style - if source is detailed, be detailed; if concise, be concise
  * Include the same examples or analogies from source when relevant
  * PRESERVE all tables, code blocks, and structured content from source in their complete markdown format
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
8. NEVER remove or summarize tables, code blocks, or structured content - keep them complete
9. Maintain all markdown formatting from source material (tables, lists, code blocks, etc.)
10. DETECT TABLES: If source contains "| ... |" patterns, include the COMPLETE markdown table in content array, don't convert to text

TONE PRESERVATION:
- Read the source material carefully and match its energy
- If it's enthusiastic, be enthusiastic. If it's clear and direct, be clear and direct.
- Preserve vivid language, interesting examples, and engaging explanations
- Don't strip away personality to make it "professional" - keep it alive!

Return ONLY valid JSON:

FOR REGULAR CONTENT (no tables):
{{
  "slide_id": "slide_XXX",
  "slide_type": "content",
  "title": "...",
  "content": ["Point 1 matching source tone", "Point 2 preserving original energy", "Point 3", "Point 4 (optional)", "Point 5 (optional)"],
  "speaker_notes": "COMPREHENSIVE explanation (8-15 sentences, detailed and thorough) that matches the tone, energy, and style of the source material. Fully explain all concepts, provide context, relationships, examples, and why each point matters. Include ALL tables, code blocks, and structured content from source in their complete markdown format. This is the speaker's complete script.",
  "image_query": "specific descriptive query or null",
  "metadata": {{
    "slide_subtype": "standard"
  }}
}}

FOR CONTENT WITH TABLES:
{{
  "slide_id": "slide_XXX",
  "slide_type": "content",
  "title": "...",
  "content": ["| Cột 1 | Cột 2 | Cột 3 | Cột 4 | Cột 5 |\\n| ----- | ----- | ----- | ----- | ----- |\\n| 1 | 2 | 3 | 4 | 5 |\\n| 1 | 2 | 3 | 4 | 5 |", "Additional context if needed", "Another point if relevant"],
  "speaker_notes": "COMPREHENSIVE explanation including table context...",
  "image_query": null,
  "metadata": {{
    "slide_subtype": "standard"
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
If image needed, create SPECIFIC query matching slide content (not generic "unit circle").
REMEMBER: ALL mathematical expressions MUST be wrapped in LaTeX $...$ or $$...$$ delimiters!"""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        data = self._parse_json_response(response.content)
        
        data = process_slide_latex(data)
        
        return SlideContent(**data)
    
    def _parse_json_response(self, response_content: str, retry_count: int = 0) -> Dict:
        content = response_content.strip()
        
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
            return json.loads(content)
        except json.JSONDecodeError as e:
            if retry_count >= 2:
                raise ValueError(f"Failed to parse JSON after {retry_count} retries: {str(e)[:200]}") from e
            
            fixed_content = self._llm_fix_json(content, str(e))
            return self._parse_json_response(fixed_content, retry_count + 1)
    
    def _llm_fix_json(self, broken_json: str, error_message: str) -> str:
        fix_prompt = f"""The following JSON has a syntax error. Fix it and return ONLY the corrected JSON.

ERROR: {error_message}

BROKEN JSON:
{broken_json[:3000]}

COMMON ISSUES TO FIX:
1. Escape backslashes in LaTeX: \\frac, \\sin, \\cos should be \\\\frac, \\\\sin, \\\\cos in JSON strings
2. Escape special characters: newlines should be \\n
3. Close unclosed strings, braces, brackets
4. Remove trailing commas before closing braces

Return ONLY the fixed valid JSON, no explanations:"""

        response = self.llm.invoke([
            {"role": "user", "content": fix_prompt}
        ])
        
        return response.content.strip()