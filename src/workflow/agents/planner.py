import llm_extension
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
import re
from src.models.context import DocumentContext
from src.utils.config import config

class PlannerAgent:
    def __init__(self, model: str = "gpt-5"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
        self.model = model
    
    def _split_into_logical_sections(self, text: str) -> List[str]:
        sections = re.split(r'\n#\s+', text)
        return [s.strip() for s in sections if len(s.strip()) > 50]
    
    def create_outline(self, context: DocumentContext) -> Dict[str, Any]:
        full_text = context.text_content.markdown
        
        text_sections = self._split_into_logical_sections(full_text)
        
        text_length = len(full_text)
        
        if text_length < 3000:
            target_main_sections = "2-3"
            target_number_slide = "3-5"
            complexity_level = "concise"
        elif text_length < 10000:
            target_main_sections = "3-4"
            target_number_slide = "5-7"
            complexity_level = "detailed"
        else:
            target_main_sections = "4-5"
            target_number_slide = "7-9"
            complexity_level = "comprehensive"

        tables_assets_info = f"# Avaliable Table \n {context.tables}\n # Avaliable Image \n {context.assets.images}"
        
        prompt = f"""
You are a senior lecture designer and slide-structure architect.
Your task is to analyze the document content and produce a pedagogically sound lecture OUTLINE that can later be converted into presentation slides.
You are creating a {complexity_level} lecture outline. Think step-by-step:

STEP 1: Analyze the document structure
The document has {len(text_sections)} main sections based on content analysis.
Document length: {text_length} characters.

FULL DOCUMENT TEXT:
{full_text}
SOME INFORMATION ABOUT TABLES and ASSETS:
{tables_assets_info}

STEP 2: Create lecture outline
Generate a hierarchical outline with EXACTLY {target_main_sections} major sections and EXACTLY {target_number_slide} total slides.

STRICT REQUIREMENTS:
1. Count of "# Title" lines = {target_main_sections} (NO MORE, NO LESS)
2. Count of ALL titles (# + ##) = {target_number_slide} (NO MORE, NO LESS)
3. Each major section = ONE core concept from the document
4. Maximum 2 heading levels:
   - Use "# Title" for major sections
   - Use "## Title" for subsections  
5. A major section may or may not have subsections
6. Do NOT combine unrelated concepts
7. Do NOT add content not in the source document
8. Do NOT include topic name itself in the outline
9. Do NOT include explanations or comments

VERIFY BEFORE SUBMITTING:
- Total "# Title" = {target_main_sections}
- Total "# Title" + "## Title" = {target_number_slide}

Output ONLY the markdown outline:
"""
        
        response = self.llm.invoke(prompt)
        outline_md = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "outline": outline_md
        } 

