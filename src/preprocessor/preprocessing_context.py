import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from src.workflow.graph import create_workflow
from src.utils.file_utils import load_json, save_json
from src.models.context import DocumentContext
from src.utils.config import config

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
        "slides": [],
        "current_section_idx": 0,
        "current_iteration": 0,
        "reviewer_feedback": None,
        "rubric_scores": None,
        # Planner loop
        "planner_iteration": 0,
        "planner_reviewer_feedback": None,
        # Best-effort tracking
        "best_plan": None,
        "best_plan_score": -1.0,
        "best_slides": None,
        "best_slides_score": -1.0,
        "best_slides_feedback": None,
    }
    
    print("✓ Executing workflow...\n")
    
    result = await workflow.ainvoke(initial_state)
    
    # Use best-effort results (highest-scoring across all iterations)
    final_slides   = result.get("best_slides")   or result["slides"]
    final_plan     = result.get("best_plan")      or result["lecture_plan"]
    final_feedback = result.get("best_slides_feedback") or result.get("reviewer_feedback")

    lecture_output = {
        "lecture_id": f"lec_{context.document_id[:8]}",
        "metadata": {
            "source_document_id": context.document_id,
            "generated_at": datetime.now().isoformat(),
            "total_slides": len(final_slides),
            "quality_score": final_feedback.overall_score if final_feedback else 0,
            "iterations": result["current_iteration"]
        },
        "slides": [s.model_dump() for s in final_slides]
    }
    
    output_path = Path(args.output) if args.output else config.LECTURES_DIR / f"{lecture_output['lecture_id']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(lecture_output, output_path)
    
    # Save outline markdown (from best plan)
    outline_md = final_plan.get("outline", "")
    outline_path = output_path.parent / f"{lecture_output['lecture_id']}_outline.md"
    outline_path.write_text(outline_md, encoding='utf-8')
    
    plan_score = (
        result["best_plan_score"]
        if result.get("best_plan_score", -1.0) >= 0 else 0.0
    )
    writer_score = result.get("best_slides_score", 0.0)
    if writer_score < 0:
        writer_score = 0.0

    print(f"\n{'='*60}")
    print(f"✓ Lecture Generated Successfully")
    print(f"{'='*60}\n")
    print(f"Output:             {output_path}")
    print(f"Outline:            {outline_path}")
    print(f"Slides:             {lecture_output['metadata']['total_slides']}")
    print(f"Plan Quality Score: {plan_score:.1f}/100")
    print(f"Quality Score:      {writer_score:.1f}/100")
    print(f"Iterations:         {lecture_output['metadata']['iterations']}")
    print()



if __name__ == "__main__":
    asyncio.run(main())

