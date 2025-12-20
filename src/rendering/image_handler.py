from pathlib import Path
from typing import Optional, Dict, Any
import httpx
import shutil
from src.models.slide import ImageReference
from src.utils.config import config

class ImageHandler:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.images_dir = output_dir / "public" / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def resolve_image_path(self, image_ref: Optional[ImageReference]) -> Optional[str]:
        if not image_ref:
            return None
        
        try:
            if image_ref.source == "original" and image_ref.image_id:
                possible_extensions = [".png", ".jpg", ".jpeg"]
                
                if not config.ASSETS_DIR.exists():
                    return None
                
                for doc_dir in config.ASSETS_DIR.iterdir():
                    if doc_dir.is_dir():
                        images_subdir = doc_dir / "images"
                        if images_subdir.exists():
                            for ext in possible_extensions:
                                original_path = images_subdir / f"{image_ref.image_id}{ext}"
                                if original_path.exists():
                                    dest_path = self.images_dir / f"{image_ref.image_id}{ext}"
                                    if not dest_path.exists():
                                        shutil.copy2(original_path, dest_path)
                                    return f"/images/{image_ref.image_id}{ext}"
                
                for ext in possible_extensions:
                    original_path = config.ASSETS_DIR / f"{image_ref.image_id}{ext}"
                    if original_path.exists():
                        dest_path = self.images_dir / f"{image_ref.image_id}{ext}"
                        if not dest_path.exists():
                            shutil.copy2(original_path, dest_path)
                        return f"/images/{image_ref.image_id}{ext}"
            
            elif image_ref.source == "tavily" and image_ref.url:
                image_name = f"tavily_{abs(hash(image_ref.url)) % 100000}.jpg"
                dest_path = self.images_dir / image_name
                if not dest_path.exists():
                    self._download_image(image_ref.url, dest_path)
                if dest_path.exists():
                    return f"/images/{image_name}"
            
            elif image_ref.source == "generated" and image_ref.path:
                source_path = Path(image_ref.path)
                if source_path.exists():
                    image_name = source_path.name
                    dest_path = self.images_dir / image_name
                    if not dest_path.exists():
                        shutil.copy2(source_path, dest_path)
                    if dest_path.exists():
                        return f"/images/{image_name}"
        except Exception as e:
            print(f"Error resolving image path: {e}")
        
        return None
    
    def _download_image(self, url: str, dest_path: Path):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            raise

