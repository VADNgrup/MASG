from openai import OpenAI
from pathlib import Path
import base64
import json
from typing import Dict, Any
from src.utils.config import config

class VisionImageClassifier:
    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = model
    
    def classify_info_density(self, image_path: Path) -> Dict[str, Any]:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        base64_image = base64.b64encode(image_bytes).decode()
        
        prompt = """Classify this image into ONE category:

Categories:
- technical_diagram: Architecture diagrams, flowcharts, system designs
- data_chart: Charts with specific data (bar, line, pie charts)
- screenshot_code: Code screenshots, terminal outputs
- conceptual_illustration: Diagrams explaining concepts (but replaceable)
- generic_illustration: General photos/illustrations
- decorative_photo: Decorative images without educational value

Return ONLY valid JSON:
{
  "type": "...",
  "confidence": 0.95,
  "reasoning": "..."
}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }],
            max_tokens=200,
            temperature=0.2
        )
        
        try:
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0]
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            print(f"Vision classifier parse error: {e}")
            return {"type": "generic_illustration", "confidence": 0.5, "reasoning": f"Parse error: {str(e)}"}

