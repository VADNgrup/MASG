from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
from src.utils.config import config

class ContentAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model
    
    def generate_slide_json(self, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = """You are a content structuring agent for presentations.

Your task: Transform lecture content into a structured JSON format optimized for slidev rendering.

AVAILABLE SLIDE TYPES:

1. **visual** - Simple visual slide
   - title: Main heading
   - description: Explanatory text  
   - image: Image filename (from lecture data)

2. **table** - Data tables
   - title: Table heading
   - headers: Column headers array
   - rows: 2D array of cell values

3. **formula** - Mathematical formulas
   - title: Heading
   - bullets: Introductory bullet points (optional)
   - formulas: LaTeX formulas WITHOUT $ delimiters

4. **cards** - Three-column feature cards (for 3-step processes)
   - title: Main heading
   - category: Badge text (optional)
   - cards: Array of {heading, description, icon, color}

5. **split_image_list** - Image + numbered list
   - title: Main heading
   - image: Image filename
   - badge: Status badge (optional)
   - items: Array of {heading, description}

6. **comparison** - Pros/cons or before/after
   - title: Main heading
   - subtitle: Subheading (optional)
   - left_title: Negative side title
   - left_items: Array of disadvantages
   - right_title: Positive side title  
   - right_items: Array of advantages

7. **stats** - Metrics showcase
   - title: Main heading
   - description: Explanatory text
   - stats: Array of {value, label, color}

IMPORTANT RULES:
- Use Vietnamese language for all content
- Formulas: Plain LaTeX WITHOUT $ or $$ (e.g., "\\sin^2 x + \\cos^2 x = 1")
- Images: Reference by filename from lecture data (e.g., "img_003_05")
- Tables: Use arrays for headers and rows
- Mix slide types appropriately for variety
- Return ONLY valid JSON

Output schema:
{
  "slides": [ {...slide objects...} ]
}
"""

        user_prompt = f"""Convert this lecture to JSON slides:

{json.dumps(lecture_data, ensure_ascii=False, indent=2)}

Generate slides following the schema. Mix slide kinds as appropriate."""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        content = response.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        slide_json = json.loads(content)
        
        self._validate_json(slide_json)
        
        return slide_json
    
    def _validate_json(self, data: Dict[str, Any]):
        text = json.dumps(data)
        if "$" in text:
            raise ValueError("Invalid content: Contains $ delimiter")
        if "<div>" in text or "</div>" in text:
            raise ValueError("Invalid content: Contains HTML tags")