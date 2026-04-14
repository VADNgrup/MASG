import base64
from typing import List, Optional, Dict, Any
from tqdm import tqdm
from src.utils.config import config
from src.utils.llm import vision_chat, b64_image

class VisionCaptionGenerator:
    def __init__(self, model: str = None):
        """
        Initialize the Vision Caption Generator.

        Args:
            model: VLM model to use (defaults to config.VLM_MODEL_NAME)
        """
        self.model = model or config.VLM_MODEL_NAME
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
            return vision_chat(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            b64_image(image_bytes),
                        ],
                    }
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            print(f"Error generating caption: {e}")
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
            return vision_chat(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            print(f"Error generating table caption: {e}")
            return f"Table: {context[:100]}..." if context else "Data table"

