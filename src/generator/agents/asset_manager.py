import shutil
from pathlib import Path
from typing import Dict, Any, List
import json

class AssetManager:
    def __init__(self, slidev_public_dir: str = "slidev/public"):
        self.public_dir = Path(slidev_public_dir)
        self.public_dir.mkdir(parents=True, exist_ok=True)
    
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
