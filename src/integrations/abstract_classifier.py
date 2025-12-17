from openai import OpenAI
from src.utils.config import config

class AbstractConceptClassifier:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = model
    
    def is_abstract(self, query: str) -> bool:
        prompt = f"""Classify if this image query describes an ABSTRACT CONCEPT or CONCRETE OBJECT:
Query: "{query}"

Abstract concepts: "future of AI", "blockchain concept", "innovation", "digital transformation"
Concrete objects: "laptop", "office building", "graph chart", "microscope"

Return ONLY ONE WORD: abstract OR concrete"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip().lower()
        return "abstract" in result

