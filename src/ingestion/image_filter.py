import io
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import numpy as np
from openai import OpenAI

from src.utils.config import config

class ImageFilter:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def pre_filter(self, image_bytes: bytes) -> Tuple[bool, str]:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            
            if width < 30 or height < 30:
                return False, "too_small"
            
            if width < 50 and height < 50:
                area = width * height
                if area < 1000:
                    return False, "too_small_area"
            
            img_array = np.array(img)
            
            if self._is_pure_single_color(img_array):
                return False, "pure_single_color"
            
            return True, "passed_pre_filter"
            
        except Exception:
            return True, "error_assume_valid"
    
    def _is_pure_single_color(self, img_array: np.ndarray) -> bool:
        if len(img_array.shape) != 3:
            return False
        
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[2]), axis=0))
        
        if unique_colors <= 2:
            return True
        
        if unique_colors <= 5:
            flat = img_array.reshape(-1, img_array.shape[2])
            unique, counts = np.unique(flat, axis=0, return_counts=True)
            most_common_count = counts.max()
            total_pixels = img_array.shape[0] * img_array.shape[1]
            
            if most_common_count / total_pixels > 0.99:
                return True
        
        return False
    
    def classify_image_content(self, image_path: Path) -> Tuple[str, float]:
        try:
            with open(image_path, "rb") as f:
                import base64
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            prompt = """Classify this image from an educational document into ONE category:

VALID categories (educational content):
- "formula": Mathematical formulas, equations, mathematical expressions
- "diagram": Charts, graphs, flowcharts, technical diagrams, geometric shapes
- "illustration": Photos, drawings with educational value
- "table_image": Tables as images
- "text_image": Important text blocks as images

INVALID categories (noise/decoration):
- "decoration": ONLY pure decorative borders, patterns, ornamental elements with NO educational value
- "header_footer": Page headers, footers, page numbers ONLY
- "noise": Completely unclear, corrupted, or meaningless images

IMPORTANT: When in doubt between valid and invalid, classify as VALID. Only mark as invalid if you are CERTAIN it has no educational value.

Respond in format: CATEGORY|confidence
Example: formula|0.95"""

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
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if '|' in result:
                category, confidence_str = result.split('|')
                category = category.strip().lower()
                confidence = float(confidence_str.strip())
            else:
                category = result.strip().lower()
                confidence = 0.5
            
            return category, confidence
            
        except Exception as e:
            return "unknown", 0.0
    
    def should_caption_image(
        self, 
        image_bytes: bytes, 
        image_path: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[str]]:
        passed_pre, reason = self.pre_filter(image_bytes)
        
        if not passed_pre:
            return False, reason, None
        
        if image_path is None:
            return True, "passed_pre_filter_only", None
        
        category, confidence = self.classify_image_content(image_path)
        
        invalid_categories = ["decoration", "header_footer", "noise"]
        
        if category in invalid_categories and confidence > 0.7:
            return False, f"classified_as_{category}", category
        
        if category in invalid_categories and confidence < 0.7:
            return True, "low_confidence_keep_it", category
        
        return True, "valid_educational_content", category

