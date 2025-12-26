import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from src.workflow.graph import create_workflow
from src.utils.file_utils import load_json, save_json
from src.models.context import DocumentContext
from src.utils.config import config
from src.optimization.lightning_setup import lightning_setup

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
        "image_decisions": [],
        "optimization_hints": {}
    }
    
    print("✓ Executing workflow...\n")
    
    if lightning_setup.is_available():
        tracer = lightning_setup.get_tracer()
        async with tracer.trace_context(name="lecture-generation"):
            result = await workflow.ainvoke(initial_state)
        
        trace_file = lightning_setup.save_traces()
        if trace_file:
            print(f"✓ Lightning traces saved to: {trace_file}")
    else:
        result = await workflow.ainvoke(initial_state)
    
    lecture_output = {
        "lecture_id": f"lec_{context.document_id[:8]}",
        "metadata": {
            "source_document_id": context.document_id,
            "generated_at": datetime.now().isoformat(),
            "total_slides": len(result["slides"]),
            "quality_score": result.get("reviewer_feedback", {}).overall_score if result.get("reviewer_feedback") else 0,
            "iterations": result["current_iteration"]
        },
        "slides": [s.model_dump() for s in result["slides"]],
        "image_stats": _compute_image_stats(result["image_decisions"]),
        "decision_logs": result["image_decisions"]
    }
    
    output_path = Path(args.output) if args.output else config.LECTURES_DIR / f"{lecture_output['lecture_id']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(lecture_output, output_path)
    
    print(f"\n{'='*60}")
    print(f"✓ Lecture Generated Successfully")
    print(f"{'='*60}\n")
    print(f"Output: {output_path}")
    print(f"Slides: {lecture_output['metadata']['total_slides']}")
    print(f"Quality Score: {lecture_output['metadata']['quality_score']:.1f}/100")
    print(f"Iterations: {lecture_output['metadata']['iterations']}")
    print(f"\n✓ Image Source Breakdown:")
    for source, count in lecture_output['image_stats'].items():
        print(f"  - {source}: {count}")
    print()

def _compute_image_stats(decisions: list) -> dict:
    stats = {"original": 0, "tavily": 0, "generated": 0, "none": 0}
    for decision in decisions:
        final_source = decision.get("final_source", "").lower()
        decision_type = decision.get("decision", "").lower()
        
        if "original" in final_source or "original" in decision_type or "force_original" in decision_type:
            stats["original"] += 1
        elif "tavily" in final_source or "search" in decision_type:
            stats["tavily"] += 1
        elif "generated" in final_source or "generated" in decision_type:
            stats["generated"] += 1
        elif final_source == "none" or not final_source:
            stats["none"] += 1
    return stats

if __name__ == "__main__":
    asyncio.run(main())

