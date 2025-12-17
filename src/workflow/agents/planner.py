from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
import re
from src.models.context import DocumentContext
from src.utils.config import config

class PlannerAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
    
    def _split_into_logical_sections(self, text: str) -> List[str]:
        sections = re.split(r'\n#{1,3}\s+', text)
        return [s.strip() for s in sections if len(s.strip()) > 50]
    
    def create_outline(self, context: DocumentContext) -> Dict[str, Any]:
        full_text = context.text_content.markdown
        
        diagrams = [img for img in context.assets.images if img.content_type in ["diagram", "technical_diagram"]]
        tables = [img for img in context.assets.images if img.content_type == "table_image"]
        
        text_sections = self._split_into_logical_sections(full_text)
        
        assets_info = f"""
Available Visual Assets:
- Diagrams: {len(diagrams)} (technical illustrations)
- Data Tables: {len(tables)} (critical data - MUST have dedicated slides)
- Total Images: {len(context.assets.images)}
"""
        
        prompt = f"""You are creating a comprehensive lecture outline. Think step-by-step:

STEP 1: Analyze the document structure
The document has {len(text_sections)} main sections based on content analysis.

FULL DOCUMENT TEXT:
{full_text}

{assets_info}

STEP 2: Identify ALL key topics that must be covered:
- Read through the entire text
- List every distinct concept, definition, property, formula
- Do NOT skip any major topic

STEP 3: Create detailed outline
REQUIREMENTS:
1. Create 8-12 sections to cover ALL content (not 4-6)
2. Each major concept gets its own section
3. Each data table gets a dedicated section
4. Include specific key_concepts from source text (not generic)

Generate structured lecture outline in JSON:
{{
  "title": "Lecture Title",
  "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
  "sections": [
    {{
      "section_id": "sec_001",
      "title": "Specific Section Title from Document",
      "estimated_slides": 1,
      "key_concepts": ["Specific concept 1", "Specific concept 2", "Specific concept 3"],
      "needs_visual": true
    }}
  ]
}}

CRITICAL: Extract section titles and key_concepts DIRECTLY from the source text.
Return ONLY valid JSON, no markdown formatting."""
        
        response = self.llm.invoke(prompt)
        
        try:
            return json.loads(response.content)
        except:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0]
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())

