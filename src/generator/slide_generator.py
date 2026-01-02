import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generator.agents.content import ContentAgent
from src.generator.agents.slidev_renderer import SlidevRenderer
from src.generator.agents.validator import SlidevValidatorAgent
from src.generator.agents.asset_manager import AssetResolver
import json
import re


def extract_lecture_id(lecture_json_path: str) -> str:
    filename = Path(lecture_json_path).stem
    match = re.search(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){0,3}', filename)
    if match:
        return match.group(0)
    return filename.replace('lec_', '')


def generate_slidev_presentation(
    lecture_json_path: str, 
    output_slides_path: str = "slidev/slides.md",
    template_name: str = "dark_modern"
):
    print("=" * 60)
    print("Slidev Presentation Generator v2.0")
    print("=" * 60)
    
    print(f"\nLoading lecture from: {lecture_json_path}")
    with open(lecture_json_path, 'r', encoding='utf-8') as f:
        lecture_data = json.load(f)
    
    lecture_id = extract_lecture_id(lecture_json_path)
    print(f"Lecture ID: {lecture_id}")
    print(f"✓ Loaded {len(lecture_data.get('slides', []))} slides")
    
    print("\nStage 1: Content Planner (LLM → Validated JSON)")
    content_agent = ContentAgent()
    slide_json = content_agent.generate_slide_json(lecture_data)
    
    json_path = lecture_json_path.replace('.json', '_slide_structure.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(slide_json, f, ensure_ascii=False, indent=2)
    print(f"✓ Generated and validated content JSON")
    
    print(f"\nStage 2: Asset Resolution")
    asset_resolver = AssetResolver()
    asset_resolver.set_lecture_context(lecture_id)
    slide_json = asset_resolver.process_slides(slide_json)
    print(f"✓ Resolved image paths")
    
    print(f"\nStage 3: Slidev Renderer (Jinja2 → Markdown)")
    print(f"  Template: {template_name}")
    renderer = SlidevRenderer(template_name=template_name, lecture_id=lecture_id)
    markdown_content = renderer.render_slidev(slide_json)
    print(f"✓ Rendered {len(markdown_content)} characters")
    
    print(f"\nStage 4: Validation & Auto-Fix")
    validator = SlidevValidatorAgent()
    result = validator.validate_and_fix(markdown_content, output_slides_path)
    
    if result["success"]:
        print(f"\n{'='*60}")
        print("SUCCESS")
        print(f"{'='*60}")
        print(f"Output: {output_slides_path}")
        print(f"Attempts: {result['attempts']}")
    else:
        print(f"\n{'='*60}")
        print("BUILD HAS ERRORS")
        print(f"{'='*60}")
        print(f"Output: {output_slides_path}")
        print(f"Attempts: {result['attempts']}")
        if result.get('parsed_errors'):
            print("Errors:")
            for err in result['parsed_errors'][:5]:
                print(f"  - [{err['type']}] {err['message'][:80]}")
    
    print("\n" + "=" * 60)
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_generator.py <lecture_json_path> [output_path]")
        sys.exit(1)
    
    lecture_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "slidev/slides.md"
    
    generate_slidev_presentation(lecture_path, output_path)
