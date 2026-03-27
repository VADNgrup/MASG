import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from src.workflow.graph import create_workflow
from src.utils.file_utils import load_json, save_json
from src.models.context import DocumentContext
from src.utils.config import config
from dataclasses import asdict

async def main():
    parser = argparse.ArgumentParser(description="Phase 2: LangGraph Workflow")
    parser.add_argument("--context", required=True, help="Path to Phase 1 context JSON")
    parser.add_argument("--output", default=None, help="Output lecture JSON path")
    args = parser.parse_args()
    
    context_data = load_json(args.context)
    context = DocumentContext(**context_data)
    
    print(f"\n{'='*60}")
    print(f"✓ Phase 2: Lecture Generation Workflow")
    print(f"{'='*60}\n")
    print(f"Source: {context.source_file}")
    print(f"Pages: {context.text_content.page_count}")
    print(f"Images: {context.metadata.total_images}")
    print(f"Tables: {context.metadata.total_tables}\n")
    
    config.validate()
    
    workflow = create_workflow()
    
    initial_state = {
        "document_context": context,
        "lecture_plan": None,
        "lecture_title": "",
        "slides": [],
        "current_section_idx": 0,
        "current_iteration": 0,
        "reviewer_feedback": None,
        # Best-effort tracking (lower score = fewer critical issues = better)
        "best_slides": None,
        "best_slides_score": float("inf"),
        "best_slides_feedback": None,
        # Plan specer output
        "slide_specs": None,
        # Planner backtrack
        "planner_backtrack_used": False,
        "coverage_feedback": None,
    }
    
    print("✓ Executing workflow...\n")
    
    result = await workflow.ainvoke(initial_state)
    
    # finalize_plan and finalize_slides nodes already restore the best versions into state
    final_slides   = result["slides"]
    final_plan     = result["lecture_plan"]
    final_feedback = result.get("reviewer_feedback")

    # Quality score: fraction of slides that passed (0.0–100.0)
    if final_feedback:
        total  = len(final_feedback.slide_reviews)
        passed = total - len(final_feedback.failed_slides)
        quality_score = round(passed / total * 100, 1) if total > 0 else 0.0
    else:
        quality_score = 0.0

    lecture_output = {
        "lecture_id": f"lec_{context.document_id[:8]}",
        "metadata": {
            "source_document_id": context.document_id,
            "generated_at": datetime.now().isoformat(),
            "total_slides": len(final_slides),
            "quality_score": quality_score,
            "iterations": result["current_iteration"]
        },
        "lecture_title": result["lecture_title"],
        "slides": [asdict(s) for s in final_slides]
    }
    
    output_path = Path(args.output) if args.output else config.LECTURES_DIR / f"{lecture_output['lecture_id']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(lecture_output, output_path)
    
    # Save outline markdown (from best plan)
    outline_md = final_plan.get("outline", "")
    outline_path = output_path.parent / f"{lecture_output['lecture_id']}_outline.md"
    outline_path.write_text(outline_md, encoding='utf-8')
    
    # Save plan spec JSON
    final_specs = result.get("slide_specs")
    if final_specs:
        def _serialize_spec(s):
            d = asdict(s)
            # Convert SlideType enum to its string value
            if hasattr(d.get("slide_type"), "value"):
                d["slide_type"] = d["slide_type"].value
            return d
        specs_data = [_serialize_spec(s) for s in final_specs]
        specs_path = output_path.parent / f"{lecture_output['lecture_id']}_plan_spec.json"
        save_json(specs_data, specs_path)
    else:
        specs_path = None
    
    # best_slides_score stores # of critical issues (lower = better)
    slides_critical = result.get("best_slides_score", float("inf"))
    slides_critical_str = str(int(slides_critical)) if slides_critical != float("inf") else "n/a"

    print(f"\n{'='*60}")
    print(f"Lecture Generated Successfully")
    print(f"{'='*60}\n")
    print(f"Output:                  {output_path}")
    print(f"Outline:                 {outline_path}")
    print(f"Plan Spec:               {specs_path}")
    print(f"Slides:                  {lecture_output['metadata']['total_slides']}")
    print(f"Quality Score:           {quality_score:.1f}% slides passed")
    print(f"Best slides critical issues: {slides_critical_str}")
    print(f"Writer iterations:       {lecture_output['metadata']['iterations']}")



if __name__ == "__main__":
    asyncio.run(main())

