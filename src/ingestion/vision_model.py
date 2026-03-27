import base64
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from openai import OpenAI
from tqdm import tqdm
from src.utils.config import config
from src.utils.parse_llm_response import clear_think

class VisionCaptionGenerator:
    def __init__(self, model: str = None):
        """
        Initialize the Vision Caption Generator.
        
        Args:
            model: VLM model to use (defaults to config.VLM_MODEL_NAME)
        """
        BASE_URL = f"{config.VLM_BASE_URL}/v1"
        API_KEY = config.VLM_API_KEY
        MODEL = config.VLM_MODEL_NAME
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
        self.model = model or MODEL
        self.max_tokens = config.VISION_MAX_TOKENS
        self.temperature = config.VISION_TEMPERATURE
    
    def generate_caption(self, image_bytes: bytes, context: str) -> str:
        """
        Generate a descriptive caption for an image based on the provided context.
        
        Args:
            image_bytes: Raw image data in bytes
            context: Contextual information about the image (e.g., surrounding text, topic)
        
        Returns:
            str: Generated caption for the image
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create prompt that combines context with image analysis
        prompt = f"""You are analyzing an image from an educational document. 

Context from the document:
{context}

Based on the context and the image content, generate a clear, concise, and descriptive caption for this image. The caption should:
1. Accurately describe what the image shows
2. Connect the image to the surrounding context
3. Be suitable for educational purposes
4. Be 2-3 sentences long

Return ONLY the caption text, without any additional formatting or explanation."""

        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract and return the caption
            caption = clear_think(response.choices[0].message.content)
            return caption
            
        except Exception as e:
            print(f"Error generating caption: {e}")
            # Return a fallback caption based on context
            return f"Image related to: {context[:100]}..." if context else "Educational image"
    
    def generate_table_caption(self, table_markdown: str, context: str) -> str:
        """
        Generate a descriptive caption for a table based on its content and context.
        
        Args:
            table_markdown: The table content in markdown format
            context: Contextual information (e.g., surrounding text from prev/next lines)
        
        Returns:
            str: Generated caption for the table
        """
        # Create prompt for table caption generation
        prompt = f"""You are analyzing a table from an educational document.

Context from the document:
{context}

Table content:
{table_markdown}

Based on the table content and surrounding context, generate a clear, concise, and descriptive caption for this table. The caption should:
1. Accurately describe what data the table presents
2. Connect the table to the surrounding context
3. Be suitable for educational purposes
4. Start with "Table:" or "Table X:" format
5. Be 1-2 sentences long

Return ONLY the caption text, without any additional formatting or explanation."""

        try:
            # Call VLM API for text-based caption generation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract and return the caption
            caption = clear_think(response.choices[0].message.content)
            return caption
            
        except Exception as e:
            print(f"Error generating table caption: {e}")
            # Return a fallback caption based on context
            return f"Table: {context[:100]}..." if context else "Data table"
