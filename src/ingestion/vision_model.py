import base64
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from openai import OpenAI
from tqdm import tqdm

from src.utils.config import config
from src.utils.file_utils import save_json, load_json
from src.utils.file_utils import save_json, load_json

class VisionCaptionGenerator:
    def __init__(self, cache_file: Optional[Path] = None):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.cache_file = cache_file
        self.cache: Dict[str, Dict[str, str]] = {}
        
        if cache_file and cache_file.exists():
            self.cache = load_json(cache_file)
    
    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _generate_caption(self, image_path: Path, prompt: str) -> str:
        base64_image = self._encode_image(image_path)
        
        try:
            response = self.client.chat.completions.create(
                model=config.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=config.VISION_MAX_TOKENS,
                temperature=config.VISION_TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating caption for {image_path.name}: {e}")
            return ""
    
    def generate_dual_captions(
        self, 
        image_path: Path, 
        image_id: str,
        content_type: Optional[str] = None
    ) -> Tuple[str, str]:
        if image_id in self.cache:
            cached = self.cache[image_id]
            return cached.get('caption_rag', ''), cached.get('caption_display', '')
        
        context_hint = ""
        if content_type:
            if content_type == "formula":
                context_hint = "This is a mathematical formula/equation. "
            elif content_type == "diagram":
                context_hint = "This is a technical diagram or chart. "
            elif content_type == "table_image":
                context_hint = "This is a table shown as an image. "
        
        rag_prompt = (
            f"{context_hint}"
            "Describe this educational image in detail with specific keywords. "
            "Include: diagram types, technical terms, numerical data, relationships shown, key concepts. "
            "Make it searchable and information-rich."
        )
        
        display_prompt = (
            f"{context_hint}"
            "Provide a brief, clear caption for this educational image (1-2 sentences). "
            "Make it concise and easy to understand."
        )
        
        caption_rag = self._generate_caption(image_path, rag_prompt)
        time.sleep(0.5)
        
        caption_display = self._generate_caption(image_path, display_prompt)
        
        self.cache[image_id] = {
            'caption_rag': caption_rag,
            'caption_display': caption_display
        }
        
        if self.cache_file:
            save_json(self.cache, self.cache_file)
        
        return caption_rag, caption_display
    
    def batch_generate_captions(
        self, 
        image_data: List[Tuple[Path, str, Optional[str]]]
    ) -> Dict[str, Tuple[str, str]]:
        results = {}
        
        for image_path, image_id, content_type in tqdm(image_data, desc="Generating captions"):
            caption_rag, caption_display = self.generate_dual_captions(
                image_path, 
                image_id, 
                content_type
            )
            results[image_id] = (caption_rag, caption_display)
            time.sleep(0.5)
        
        return results

