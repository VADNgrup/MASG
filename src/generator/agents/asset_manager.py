import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import re


class AssetResolver:
    def __init__(self, base_assets_dir: str = "data/assets", public_dir: str = "slidev/public/assets"):
        self.base_assets_dir = Path(base_assets_dir)
        self.public_dir = Path(public_dir)
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.image_cache: Dict[str, str] = {}
        self.lecture_id: Optional[str] = None
    
    def set_lecture_context(self, lecture_id: str):
        self.lecture_id = lecture_id
        self.image_cache.clear()
        
        lecture_assets = self.base_assets_dir / lecture_id
        if lecture_assets.exists():
            self._scan_and_copy_assets(lecture_assets)
        
        generated_assets = self.base_assets_dir / "generated"
        if generated_assets.exists():
            self._scan_and_copy_assets(generated_assets)
    
    def _scan_and_copy_assets(self, source_dir: Path):
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg']:
            for img_file in source_dir.rglob(ext):
                image_id = img_file.stem
                dest_path = self.public_dir / img_file.name
                
                if not dest_path.exists():
                    shutil.copy2(img_file, dest_path)
                
                self.image_cache[image_id] = f"/assets/{img_file.name}"
    
    def resolve(self, image_ref: Optional[str]) -> Optional[str]:
        if not image_ref:
            return None
        
        if image_ref.startswith(('http://', 'https://', '/')):
            return image_ref
        
        image_ref = image_ref.replace('/assets/', '').replace('assets/', '')
        image_id = Path(image_ref).stem
        
        if image_id in self.image_cache:
            return self.image_cache[image_id]
        
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
            for search_dir in [self.base_assets_dir, self.public_dir.parent]:
                for img_file in search_dir.rglob(f"{image_id}{ext}"):
                    dest_path = self.public_dir / img_file.name
                    if not dest_path.exists():
                        shutil.copy2(img_file, dest_path)
                    resolved = f"/assets/{img_file.name}"
                    self.image_cache[image_id] = resolved
                    return resolved
        
        return f"/assets/{image_ref}.png"
    
    def process_slides(self, slides_data: Dict[str, Any]) -> Dict[str, Any]:
        for slide in slides_data.get("slides", []):
            if "image" in slide and slide["image"]:
                slide["image"] = self.resolve(slide["image"])
            
            if "cards" in slide:
                for card in slide["cards"]:
                    if "image" in card:
                        card["image"] = self.resolve(card["image"])
            
            if "stats" in slide:
                for stat in slide["stats"]:
                    if "image" in stat:
                        stat["image"] = self.resolve(stat["image"])
        
        return slides_data
    
    def clear_public_assets(self):
        if self.public_dir.exists():
            for f in self.public_dir.glob("*"):
                if f.is_file():
                    f.unlink()


class AssetManager:
    def __init__(self, slidev_public_dir: str = "slidev/public"):
        self.public_dir = Path(slidev_public_dir)
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.resolver = AssetResolver(public_dir=str(self.public_dir / "assets"))
    
    def clear_old_images(self):
        for img_file in self.public_dir.glob("img_*"):
            img_file.unlink()
    
    def copy_lecture_images(self, lecture_data: Dict[str, Any], lecture_json_path: str) -> Dict[str, str]:
        lecture_path = Path(lecture_json_path)
        lecture_id = lecture_data.get('lecture_title', '')
        data_assets_dir = lecture_path.parent.parent / 'assets'
        
        target_asset_dir = None
        if lecture_id and (data_assets_dir / lecture_id / 'images').exists():
            target_asset_dir = data_assets_dir / lecture_id / 'images'
        else:
            target_asset_dir = lecture_path.parent / 'assets'
            
        print(f"Looking for assets in: {target_asset_dir}")
        
        image_mapping = {}
        
        for slide in lecture_data.get('slides', []):
            visual_asset = slide.get('visual_asset')
            if not visual_asset:
                continue
            
            image_id = visual_asset.get('image_id')
            if not image_id:
                continue
            
            source_path = None
            if target_asset_dir.exists():
                for ext in ['.png', '.jpg', '.jpeg']:
                    potential_path = target_asset_dir / f"{image_id}{ext}"
                    if potential_path.exists():
                        source_path = potential_path
                        break
            
            if source_path and source_path.exists():
                dest_path = self.public_dir / source_path.name
                shutil.copy2(source_path, dest_path)
                image_mapping[image_id] = f"/{source_path.name}"
            else:
                 print(f"Warning: Image {image_id} not found in {target_asset_dir}")
        
        return image_mapping
    
    def process_lecture_assets(self, lecture_data: Dict[str, Any], lecture_json_path: str) -> Dict[str, Any]:
        self.clear_old_images()
        
        image_mapping = self.copy_lecture_images(lecture_data, lecture_json_path)
        
        for slide in lecture_data.get('slides', []):
            visual_asset = slide.get('visual_asset')
            if visual_asset and visual_asset.get('image_id'):
                image_id = visual_asset['image_id']
                if image_id in image_mapping:
                    visual_asset['url'] = image_mapping[image_id]
        
        return lecture_data
