import llm_extension
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
import re
from src.models.context import DocumentContext
from src.utils.config import config

class PlannerAgent:
    def __init__(self, model):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
        self.model = model
    
    def _split_into_logical_sections(self, text: str) -> List[str]:
        sections = re.split(r'\n#\s+', text)
        return [s.strip() for s in sections if len(s.strip()) > 50]
    
    def create_outline(self, context: DocumentContext, feedback: str = None) -> Dict[str, Any]:
        full_text = context.text_content.markdown
        
        text_sections = self._split_into_logical_sections(full_text)
        
        text_length = len(full_text)
        
        if text_length < 3000:
            target_main_sections = "2"
            complexity_level = "concise"
        elif text_length < 10000:
            target_main_sections = "3"
            complexity_level = "detailed"
        else:
            target_main_sections = "4"
            complexity_level = "comprehensive"

        tables_assets_info = f"# Avaliable Table \n {context.tables}\n # Avaliable Image \n {context.assets.images}"
        
        feedback_block = ""
        if feedback:
            feedback_block = f"""
 REVISION FEEDBACK FROM PREVIOUS OUTLINE REVIEW:
{feedback}

Apply all the suggestions above when generating this revised outline.
"""
        
        prompt = f"""
# ROLE
You are a senior lecture designer and slide-structure architect.
# TASK
Your task is to analyze the document content and produce a pedagogically sound lecture OUTLINE that can later be converted into presentation slides. 
You are creating a {complexity_level} lecture outline. Think step-by-step:
# HOW TO PROCESS INPUTS
## STEP 1: Analyze the document structure
The document has {len(text_sections)} main sections based on content analysis. Document length: {text_length} characters.
FULL DOCUMENT TEXT:
{full_text}
SOME INFORMATION ABOUT TABLES and ASSETS:
{tables_assets_info}
SOME FEEDBACK FROM PREVIOUS OUTLINE TO FIX AND UPGRADE:
{feedback_block}
## STEP 2: Create lecture outline
Generate a hierarchical outline with EXACTLY {target_main_sections} major sections.
# VERY STRICT REQUIREMENTS:
1. Language: same language as the document.
2. The length of a title is a maximum of 8 words.
3. Count of "# Title" lines equals to {target_main_sections}, NO MORE, NO LESS.
4. Each major section = ONE core concept from the document. No two major sections should overlap in their core concepts.
5. Maximum 2 heading levels:
   - Use "# Title" for major sections
   - Use "## Title" for subsections  
6. A major section may or may not have subsections. If it has subsections, it MUST have at least 2 subsections (never just 1)
7. Do NOT combine unrelated concepts
8. Do NOT add content not in the source document
9. Do NOT include topic name itself in the outline
10. ONLY return markdown outline,Do NOT include explanations or comments
# EXAMPLE OUTPUT:
# Title 1
## Subtitle 1.1
## Subtitle 1.2
# Title 2
## Subtitle 2.1
## Subtitle 2.2

Output ONLY the markdown outline:
"""
        response = self.llm.invoke(prompt)
        outline_md = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "outline": outline_md
        }

