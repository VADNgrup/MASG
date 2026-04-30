import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from src.workflow.graph import create_workflow
from src.utils.file_utils import load_json, save_json
from src.models.context import DocumentContext
from src.utils.config import config, Config
from dataclasses import asdict

def clean_repetition(text: str) -> str:
    """Detect and remove extreme word repetitions often caused by extraction tool loops."""
    words = text.split()
    if not words: return text
    cleaned = []
    i = 0
    while i < len(words):
        word = words[i]
        j = i + 1
        count = 1
        while j < len(words) and words[j] == word:
            count += 1
            j += 1
        cleaned.append(word)
        if count > 3: # If a word repeats more than 3 times consecutively, it's likely a loop
            i = j
        else:
            i += 1
    return " ".join(cleaned)

async def preprocess_context(context, output=None):
    print(f"\n{'=' * 60}")
    print(f'Phase 2: Lecture Generation Workflow')
    print(f"{'=' * 60}\n")
    context_data = load_json(context)
    
    # Clean repetition loops before checking length
    context_data['text_content']['markdown'] = clean_repetition(context_data['text_content']['markdown'])
    
    # Increase limit to 100k characters for technical/complex documents
    if len(context_data['text_content']['markdown']) < 512 or len(context_data['text_content']['markdown']) > 100000:
        print(f"[SKIP] Lecture is too short or too long ({len(context_data['text_content']['markdown'])} chars)")
        return (None, False)
    context = DocumentContext(**context_data)
    lecture_path = Path(Config.LECTURES_DIR / f'{context.document_id}' / f'{context.document_id}.json')
    if Path(lecture_path).exists():
        print(f'[SKIP] Lecture has id {context.document_id} already exists in lecture directory')
        print(f"\n{'=' * 60}")
        print(f'End Phase 2: Generated Lecture')
        print(f"\n{'=' * 60}")
        return (lecture_path, True)
    print(f'Source: {context.source_file}')
    print(f'Pages: {context.text_content.page_count}')
    print(f'Images: {context.metadata.total_images}')
    print(f'Tables: {context.metadata.total_tables}\n')
    config.validate()
    workflow = create_workflow()
    initial_state = {'document_context': context, 'lecture_plan': None, 'lecture_title': '', 'slides': [], 'reviewer_feedback': None, 'slide_specs': None}
    result = await workflow.ainvoke(initial_state)
    final_slides = result['slides']
    final_plan = result['lecture_plan']
    final_feedback = result.get('reviewer_feedback')
    if final_feedback:
        total = len(final_feedback.slide_reviews)
        passed = total - len(final_feedback.failed_slides)
        quality_score = round(passed / total * 100, 1) if total > 0 else 0.0
    else:
        quality_score = 0.0
    lecture_output = {'lecture_id': context.document_id, 'metadata': {'source_document_id': context.document_id, 'generated_at': datetime.now().isoformat(), 'total_slides': len(final_slides), 'quality_score': quality_score, 'iterations': 1}, 'lecture_title': result['lecture_title'], 'slides': [asdict(s) for s in final_slides]}
    output_save_path = Path(output) if output else config.LECTURES_DIR / f"{lecture_output['lecture_id']}"
    output_save_path.mkdir(parents=True, exist_ok=True)
    lecture_json_path = output_save_path / f"{lecture_output['lecture_id']}.json"
    save_json(lecture_output, lecture_json_path)
    outline_md = final_plan.get('outline', '')
    outline_path = output_save_path / f"{lecture_output['lecture_id']}_outline.md"
    outline_path.write_text(outline_md, encoding='utf-8')
    final_specs = result.get('slide_specs')
    if final_specs:

        def _serialize_spec(s):
            d = asdict(s)
            if hasattr(d.get('slide_type'), 'value'):
                d['slide_type'] = d['slide_type'].value
            return d
        specs_data = [_serialize_spec(s) for s in final_specs]
        specs_path = output_save_path / f"{lecture_output['lecture_id']}_plan_spec.json"
        save_json(specs_data, specs_path)
    else:
        specs_path = None
    print(f"\n{'=' * 60}")
    print(f'Lecture Generated Successfully')
    print(f"{'=' * 60}\n")
    print(f'Output:                  {output_save_path}')
    print(f'Outline:                 {outline_path}')
    print(f'Plan Spec:               {specs_path}')
    print(f"Slides:                  {lecture_output['metadata']['total_slides']}")
    print(f'Quality Score:           {quality_score:.1f}% slides passed')
    print(f"\n{'=' * 60}")
    print(f'End Phase 2: Generated Lecture')
    print(f"\n{'=' * 60}")
    return (lecture_json_path, True)

async def main():
    parser = argparse.ArgumentParser(description='Phase 2: LangGraph Workflow')
    parser.add_argument('--context', required=True, help='Path to Phase 1 context JSON')
    parser.add_argument('--output', default=None, help='Output lecture JSON path')
    args = parser.parse_args()
    (context, output) = (args.context, args.output)
    await preprocess_context(context, output)
if __name__ == '__main__':
    asyncio.run(main())