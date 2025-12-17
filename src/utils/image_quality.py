from PIL import Image
from pathlib import Path

class ImageQualityAssessor:
    @staticmethod
    def assess_quality(image_path: Path) -> float:
        img = Image.open(image_path)
        width, height = img.size
        
        pixel_count = width * height
        
        if pixel_count >= 200 * 200:
            return 0.7
        elif pixel_count >= 150 * 150:
            return 0.6
        else:
            return 0.5

