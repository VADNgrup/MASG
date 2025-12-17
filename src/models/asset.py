from typing import List, Optional
from pydantic import BaseModel, Field

class AssetMetadata(BaseModel):
    width: int
    height: int
    format: str
    file_size_kb: float

class ImageAsset(BaseModel):
    image_id: str
    file_path: str
    page_number: int
    priority: int = Field(default=1)
    caption_rag: Optional[str] = None
    caption_display: Optional[str] = None
    metadata: AssetMetadata
    content_type: Optional[str] = None
    is_decoration: bool = False

class AssetCollection(BaseModel):
    images: List[ImageAsset] = Field(default_factory=list)
    
    def add_image(self, image: ImageAsset) -> None:
        self.images.append(image)
    
    def get_by_id(self, image_id: str) -> Optional[ImageAsset]:
        for image in self.images:
            if image.image_id == image_id:
                return image
        return None
    
    def get_by_page(self, page_number: int) -> List[ImageAsset]:
        return [img for img in self.images if img.page_number == page_number]

