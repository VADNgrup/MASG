from openai import OpenAI
from pathlib import Path
import httpx
from datetime import datetime
from src.utils.config import config

class GenAIImageGenerator:
    def __init__(self, provider: str = "dalle3"):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.provider = provider
    
    async def generate(self, prompt: str, style: str = "educational") -> str:
        enhanced_prompt = f"Educational illustration for: {prompt}. Modern, clean, professional style suitable for academic presentations. High quality, clear composition."
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        
        config.GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.png"
        output_path = config.GENERATED_IMAGES_DIR / filename
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            img_response = await http_client.get(image_url)
            with open(output_path, "wb") as f:
                f.write(img_response.content)
        
        return str(output_path)

