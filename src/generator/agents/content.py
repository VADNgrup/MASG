import pinkyne_extension
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
import re
from src.utils.config import config
from src.models.slide_schemas import SlidesDocument, get_schema_for_prompt


class ContentAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model
    
    def _preprocess_lecture_content(self, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
        def fix_latex_in_text(text: str) -> str:
            if not text or not isinstance(text, str):
                return text
            
            for func in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'log', 'ln']:
                text = re.sub(rf'(?<![\\$])(?<!\w){func}(?=[\s\(\^²³])', rf'$\\{func}$', text, flags=re.IGNORECASE)
            
            text = re.sub(r'(?<!\$)([a-zA-Z])\^(\d)', r'$\1^{\2}$', text)
            text = re.sub(r'(?<!\$)(\d+)°', r'$\1^{\\circ}$', text)
            
            greek_map = {'α': r'\alpha', 'β': r'\beta', 'π': r'\pi', 'θ': r'\theta', 'Â': r'\alpha', 'Ñ': r'\pi'}
            for greek, latex in greek_map.items():
                if greek in text and f'${latex}$' not in text:
                    text = text.replace(greek, f'${latex}$')
            
            text = re.sub(r'≠', r'$\\neq$', text)
            text = re.sub(r'≤', r'$\\leq$', text)
            text = re.sub(r'≥', r'$\\geq$', text)
            
            text = re.sub(r'\$\$+', '$', text)
            
            return text
        
        def process_dict(d: Dict) -> Dict:
            result = {}
            for key, value in d.items():
                if isinstance(value, str):
                    result[key] = fix_latex_in_text(value)
                elif isinstance(value, list):
                    result[key] = [fix_latex_in_text(item) if isinstance(item, str) else process_dict(item) if isinstance(item, dict) else item for item in value]
                elif isinstance(value, dict):
                    result[key] = process_dict(value)
                else:
                    result[key] = value
            return result
        
        return process_dict(lecture_data)
    
    def generate_slide_json(self, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
        lecture_data = self._preprocess_lecture_content(lecture_data)
        
        schema_docs = get_schema_for_prompt()
        
        system_prompt = f"""You are a content structuring agent for presentations.

Your task: Transform lecture content into a structured JSON format optimized for slidev rendering.

{schema_docs}

IMPORTANT RULES:
- Use Vietnamese language for all content
- Formulas: Plain LaTeX WITHOUT $ or $$ delimiters (they will be added during rendering)
- Use proper LaTeX commands: \\sin, \\cos, \\tan, \\frac{{}}{{}}, etc.
- Convert plain text math to LaTeX: "sin²x" → "\\sin^2 x", "cosα" → "\\cos \\alpha"
- Images: Reference by filename from lecture data (e.g., "img_003_05")
- Tables: Use arrays for headers and rows
- Mix slide types appropriately for variety
- Each slide MUST have "slide_type" field
- Return ONLY valid JSON

Output format:
{{
  "slides": [ {{...slide objects...}} ]
}}
"""

        user_prompt = f"""Convert this lecture to JSON slides:

{json.dumps(lecture_data, ensure_ascii=False, indent=2)}

Generate slides following the exact schema. Mix slide kinds as appropriate for the content.
IMPORTANT: Convert ALL mathematical expressions to proper LaTeX format (without $ delimiters)."""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        content = response.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        raw_json = json.loads(content)
        
        validated = SlidesDocument.parse_slides(raw_json)
        
        return validated.model_dump(mode='json', exclude_none=True)