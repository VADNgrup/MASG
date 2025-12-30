import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generator.agents.content import ContentAgent
from src.generator.agents.markdown import MarkdownAgent
from src.generator.agents.validator import SlidevValidatorAgent
import json

def generate_slidev_presentation(lecture_json_path: str, output_slides_path: str = "slidev/slides.md"):
    print("=" * 60)
    print("Slidev Presentation Generator")
    print("=" * 60)
    
    print(f"\nLoading lecture from: {lecture_json_path}")
    with open(lecture_json_path, 'r', encoding='utf-8') as f:
        lecture_data = json.load(f)
    
    is_design_ready = False
    if 'slides' in lecture_data and lecture_data['slides']:
        first_slide = lecture_data['slides'][0]
        if 'slide_number' in first_slide and 'components' in first_slide:
            is_design_ready = True
            print(f"✓ Detected design-ready format with {lecture_data.get('total_slides', len(lecture_data['slides']))} slides")
        else:
            print(f"✓ Loaded {len(lecture_data.get('slides', []))} slides")
    
    if is_design_ready:
        print("\nSkipping Step 1: Input is already in design-ready format")
        design_ready_data = lecture_data
    else:
        print("\nStep 1: Optimizing content with ContentAgent...")
        content_agent = ContentAgent()
        design_ready_data = content_agent.process_lecture(lecture_data)
        
        simplified_path = lecture_json_path.replace('.json', '_design_ready.json')
        with open(simplified_path, 'w', encoding='utf-8') as f:
            json.dump(design_ready_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved design-ready JSON to: {simplified_path}")
    
    print("\nStep 2: Generating Slidev markdown with MarkdownAgent...")
    markdown_agent = MarkdownAgent()
    markdown_content = markdown_agent.generate_slidev_markdown(design_ready_data)
    print(f"✓ Generated {len(markdown_content)} characters of markdown")
    
    print("\nStep 3: Validating and fixing with SlidevValidatorAgent...")
    validator = SlidevValidatorAgent()
    result = validator.validate_and_fix(markdown_content, output_slides_path)
    
    if result["success"]:
        print(f"\nSUCCESS! Presentation generated successfully")
        print(f"   Attempts: {result['attempts']}")
        print(f"   Output: {output_slides_path}")
    else:
        print(f"\nWARNING: Build has errors after {result['attempts']} attempts")
        print(f"   Output saved to: {output_slides_path}")
        print(f"   Errors: {result['errors']['error_output'][:200]}...")
    
    print("\n" + "=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    lecture_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "slidev/slides.md"
    
    generate_slidev_presentation(lecture_path, output_path)
