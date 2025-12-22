from pathlib import Path
from typing import Optional
import json
from src.models.slide import LectureOutput
from src.rendering.image_handler import ImageHandler
from src.rendering.markdown_converter import MarkdownConverter
from src.rendering.slidev_generator import SlidevGenerator
from src.rendering.theme_setup import ThemeSetup
from src.rendering.slide_optimizer import SlideOptimizerAgent
from src.rendering.cover_generator import generate_cover_slide
from src.rendering.end_slide_generator import generate_end_slide
from src.rendering.theme_selector import ThemeSelector
from src.rendering.intro_slide_generator import IntroSlideGenerator

class Renderer:
    def __init__(self, output_dir: Path, use_optimizer: bool = True):
        self.output_dir = output_dir
        self.image_handler = ImageHandler(output_dir)
        self.slidev_generator = SlidevGenerator(output_dir)
        self.theme_setup = ThemeSetup(output_dir)
        self.optimizer_agent = SlideOptimizerAgent() if use_optimizer else None
        self.theme_selector = ThemeSelector()
        self.intro_generator = IntroSlideGenerator()
        self.markdown_converter = MarkdownConverter()
    
    def render(self, lecture_json: dict) -> Path:
        self.slidev_generator.create_project_structure()
        
        lecture_title = lecture_json.get("metadata", {}).get("title", "Lecture") if isinstance(lecture_json.get("metadata"), dict) else "Lecture"
        
        selected_theme = self.theme_selector.select_theme(lecture_json)
        theme_config = self.theme_selector.get_theme_config(selected_theme)
        
        self.slidev_generator.create_package_json(lecture_title, selected_theme)
        self.slidev_generator.create_vite_config()
        
        slides = lecture_json.get("slides", [])
        first_slide_title = slides[0].get("title", "") if slides else ""
        background_query = f"{lecture_title} {first_slide_title}" if first_slide_title else lecture_title
        background_url = self.image_handler.get_background_image(background_query)
        
        cover_slide = generate_cover_slide(lecture_json, selected_theme, theme_config, background_url)
        intro_slide = self.intro_generator.generate(lecture_json)
        markdown_content = self.markdown_converter.convert_lecture_to_slidev(lecture_json, self.image_handler, self.optimizer_agent)
        end_slide = generate_end_slide(lecture_title)
        
        slides_md_path = self.output_dir / "slides.md"
        
        with open(slides_md_path, "w", encoding="utf-8") as f:
            f.write(cover_slide)
            f.write(intro_slide)
            f.write("\n---\n\n")
            f.write(markdown_content)
            f.write("\n---\n\n")
            f.write(end_slide)
        
        print(f"Slidev slides generated with theme: {selected_theme}")
        print(f"   - Cover slide: OK")
        print(f"   - Intro slide: OK")
        print(f"   - Content slides: {len(slides)}")
        print(f"   - End slide: OK")
        return slides_md_path

