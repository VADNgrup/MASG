import argparse
import json
from pathlib import Path
from src.rendering.renderer import Renderer

def main():
    parser = argparse.ArgumentParser(description="Generate Slidev presentation from lecture JSON")
    parser.add_argument("--lecture", type=str, required=True, help="Path to lecture JSON file")
    parser.add_argument("--output", type=str, default="output", help="Output directory for Slidev project")
    
    args = parser.parse_args()
    
    lecture_path = Path(args.lecture)
    if not lecture_path.exists():
        print(f"Error: Lecture file not found: {lecture_path}")
        return
    
    with open(lecture_path, "r", encoding="utf-8") as f:
        lecture_json = json.load(f)
    
    output_dir = Path(args.output)
    
    renderer = Renderer(output_dir)
    slides_md_path = renderer.render(lecture_json)
    
    print(f"Slidev presentation generated successfully!")
    print(f"Output directory: {output_dir}")
    print(f"Slides file: {slides_md_path}")
    print(f"\nTo run the presentation:")
    print(f"  cd {output_dir}")
    print(f"  npm install")
    print(f"  npm run dev")

if __name__ == "__main__":
    main()

