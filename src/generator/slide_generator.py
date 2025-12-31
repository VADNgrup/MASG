import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generator.agents.content import ContentAgent
from src.generator.agents.slidev_renderer import SlidevRenderer
from src.generator.agents.validator import SlidevValidatorAgent
import json

def generate_slidev_presentation(
    lecture_json_path: str, 
    output_slides_path: str = "slidev/slides.md",
    template_name: str = "dark_modern"
):
    print("=" * 60)
    print("Slidev Presentation Generator")
    print("=" * 60)
    
    print(f"\nLoading lecture from: {lecture_json_path}")
    with open(lecture_json_path, 'r', encoding='utf-8') as f:
        lecture_data = json.load(f)
    
    print(f"✓ Loaded {len(lecture_data.get('slides', []))} slides")
    
    print("\nStage 1: Content Planner (LLM → JSON)")
    content_agent = ContentAgent()
    slide_json = content_agent.generate_slide_json(lecture_data)
    
    json_path = lecture_json_path.replace('.json', '_slide_structure.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(slide_json, f, ensure_ascii=False, indent=2)
    print(f"✓ Generated content JSON")
    
    print(f"\nStage 2: Slidev Renderer (Python → Markdown)")
    print(f"  Template: {template_name}")
    renderer = SlidevRenderer(template_name=template_name)
    markdown_content = renderer.render_slidev(slide_json)
    print(f"✓ Rendered {len(markdown_content)} characters")
    
    print(f"\nStage 3: Validation")
    validator = SlidevValidatorAgent()
    result = validator.validate_and_fix(markdown_content, output_slides_path)
    
    if result["success"]:
        print(f"\nSUCCESS")
        print(f"Output: {output_slides_path}")
    else:
        print(f"\nBuild has errors")
        print(f"   Check: {output_slides_path}")
    
    print("\n" + "=" * 60)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
       sys.exit(1)
    
    lecture_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "slidev/slides.md"
    
    generate_slidev_presentation(lecture_path, output_path)
