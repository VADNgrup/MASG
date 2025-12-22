from PIL import Image, ImageStat
from pathlib import Path
import numpy as np

class ImageQualityAssessor:
    @staticmethod
    def assess_quality(image_path: Path) -> float:
        try:
            img = Image.open(image_path)
            width, height = img.size
            pixel_count = width * height
            
            img_rgb = img.convert('RGB')
            
            resolution_score = ImageQualityAssessor._score_resolution(width, height)
            sharpness_score = ImageQualityAssessor._score_sharpness(img_rgb)
            contrast_score = ImageQualityAssessor._score_contrast(img_rgb)
            
            quality = (resolution_score * 0.4 + sharpness_score * 0.4 + contrast_score * 0.2)
            
            return min(max(quality, 0.0), 1.0)
        except Exception as e:
            print(f"Image quality assessment error for {image_path}: {e}")
            return 0.5
    
    @staticmethod
    def _score_resolution(width: int, height: int) -> float:
        """Score based on resolution: higher resolution = better quality"""
        pixel_count = width * height
        
        if pixel_count >= 500 * 500:
            return 1.0
        elif pixel_count >= 300 * 300:
            return 0.9
        elif pixel_count >= 200 * 200:
            return 0.75
        elif pixel_count >= 150 * 150:
            return 0.6
        elif pixel_count >= 100 * 100:
            return 0.5
        else:
            return 0.3
    
    @staticmethod
    def _score_sharpness(img: Image.Image) -> float:
        """Score based on image sharpness using variance of Laplacian"""
        try:
            img_array = np.array(img.convert('L'))
            
            laplacian = np.array([
                [0, -1, 0],
                [-1, 4, -1],
                [0, -1, 0]
            ])
            
            laplacian_result = np.abs(np.convolve(img_array.flatten(), laplacian.flatten(), mode='valid'))
            variance = np.var(laplacian_result)
            
            if variance > 500:
                return 1.0
            elif variance > 300:
                return 0.8
            elif variance > 150:
                return 0.6
            elif variance > 50:
                return 0.4
            else:
                return 0.3
        except:
            return 0.6
    
    @staticmethod
    def _score_contrast(img: Image.Image) -> float:
        """Score based on contrast (standard deviation of pixel values)"""
        try:
            stat = ImageStat.Stat(img)
            std_dev = np.mean([stat.stddev[i] for i in range(len(stat.stddev))])
            
            if std_dev > 60:
                return 1.0
            elif std_dev > 45:
                return 0.8
            elif std_dev > 30:
                return 0.6
            elif std_dev > 15:
                return 0.4
            else:
                return 0.3
        except:
            return 0.6

