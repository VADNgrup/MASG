from pathlib import Path
from typing import Optional
import json
from src.models.slide import LectureOutput
from src.rendering.image_handler import ImageHandler
from src.rendering.markdown_converter import convert_lecture_to_slidev
from src.rendering.slidev_generator import SlidevGenerator
from src.rendering.theme_setup import ThemeSetup
from src.rendering.slide_optimizer import SlideOptimizerAgent
from src.rendering.cover_generator import generate_cover_slide

class Renderer:
    def __init__(self, output_dir: Path, use_optimizer: bool = True):
        self.output_dir = output_dir
        self.image_handler = ImageHandler(output_dir)
        self.slidev_generator = SlidevGenerator(output_dir)
        self.theme_setup = ThemeSetup(output_dir)
        self.optimizer_agent = SlideOptimizerAgent() if use_optimizer else None
    
    def render(self, lecture_json: dict) -> Path:
        self.slidev_generator.create_project_structure()
        
        lecture_title = lecture_json.get("metadata", {}).get("title", "Lecture") if isinstance(lecture_json.get("metadata"), dict) else "Lecture"
        self.slidev_generator.create_package_json(lecture_title)
        self.slidev_generator.create_vite_config()
        self.slidev_generator.create_tailwind_config()
        
        cover_slide = generate_cover_slide(lecture_json)
        markdown_content = convert_lecture_to_slidev(lecture_json, self.image_handler, self.optimizer_agent)
        
        slides_md_path = self.output_dir / "slides.md"
        
        with open(slides_md_path, "w", encoding="utf-8") as f:
            f.write(cover_slide)
            f.write(markdown_content)
        
        return slides_md_path

