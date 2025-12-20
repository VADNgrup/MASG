from pathlib import Path
from typing import Optional
import shutil
from src.utils.config import config

class SlidevGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_project_structure(self):
        (self.output_dir / "public" / "images").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "components").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "layouts").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "themes" / "lecture").mkdir(parents=True, exist_ok=True)
        
        self._copy_layouts()
        self._copy_components()
        self._copy_styles()
    
    def _copy_layouts(self):
        source_layouts = Path(__file__).parent / "layouts"
        target_layouts = self.output_dir / "layouts"
        
        if source_layouts.exists():
            for layout_file in source_layouts.glob("*.vue"):
                shutil.copy2(layout_file, target_layouts / layout_file.name)
            for layout_file in source_layouts.glob("*.ts"):
                shutil.copy2(layout_file, target_layouts / layout_file.name)
    
    def _copy_components(self):
        source_components = Path(__file__).parent / "components"
        target_components = self.output_dir / "components"
        
        if source_components.exists():
            for component_file in source_components.glob("*.vue"):
                shutil.copy2(component_file, target_components / component_file.name)
            for component_file in source_components.glob("*.ts"):
                shutil.copy2(component_file, target_components / component_file.name)
    
    def _copy_styles(self):
        source_styles = Path(__file__).parent / "styles"
        target_styles = self.output_dir / "styles"
        
        if source_styles.exists():
            target_styles.mkdir(parents=True, exist_ok=True)
            for style_file in source_styles.glob("*.css"):
                shutil.copy2(style_file, target_styles / style_file.name)
    
    def create_package_json(self, lecture_title: str = "Lecture"):
        package_json = {
            "name": "lecture-slides",
            "version": "1.0.0",
            "description": f"{lecture_title} - Generated with lecture-gen",
            "scripts": {
                "dev": "slidev",
                "build": "slidev build",
                "export": "slidev export"
            },
            "dependencies": {
                "@slidev/cli": "^0.47.0",
                "@slidev/theme-default": "*"
            },
            "devDependencies": {
                "tailwindcss": "^3.0.0"
            }
        }
        
        import json
        package_json_path = self.output_dir / "package.json"
        with open(package_json_path, "w", encoding="utf-8") as f:
            json.dump(package_json, f, indent=2, ensure_ascii=False)
        
        return package_json_path
    
    def create_vite_config(self):
        vite_config = """import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, './')
    }
  },
  css: {
    postcss: {
      plugins: [
        require('tailwindcss'),
      ],
    },
  },
})
"""
        vite_config_path = self.output_dir / "vite.config.ts"
        with open(vite_config_path, "w", encoding="utf-8") as f:
            f.write(vite_config)
        
        return vite_config_path
    
    def create_tailwind_config(self):
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './slides.md',
    './layouts/**/*.vue',
    './components/**/*.vue',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
        tailwind_config_path = self.output_dir / "tailwind.config.js"
        with open(tailwind_config_path, "w", encoding="utf-8") as f:
            f.write(tailwind_config)
        
        return tailwind_config_path

