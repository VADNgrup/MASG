from langgraph.graph import StateGraph, END
from typing import Dict, Any
import json
from src.workflow.state import WorkflowState
from src.workflow.agents.planner import PlannerAgent
from src.workflow.agents.writer import WriterAgent
from src.workflow.agents.writer_reviewer import ReviewerAgent
from src.workflow.agents.writer_refiner import WriterRefinerAgent
from src.workflow.agents.plan_specer import PlanSpecerAgent
from src.models.feedback import WriterReview
from src.utils.config import Config


def _print_writer_review(label: str, review: WriterReview) -> None:
    failed = review.failed_slides
    total  = len(review.slide_reviews)
    print(f"\n  {'─'*50}")
    print(f"  {label}:  {total - len(failed)}/{total} slides passed")
    for sr in review.slide_reviews:
        status = "✓" if sr.passed else "✗"
        n_crit  = len(sr.convincing_critical_issues)
        n_major = len([i for i in sr.convincing_issues if i.severity.value == "major"])
        n_min   = len(sr.minor_issues)
        print(f"    {status} Slide {sr.slide_index:>2}: '{sr.slide_title[:35]}'  "
              f"critical={n_crit}  major={n_major}  minor={n_min}")
    print(f"  {'─'*50}")
    print(f"  Decision: {'ACCEPT' if review.passed else 'RETRY'}  "
          f"(critical={review.convincing_critical_count}  "
          f"major={review.convincing_major_count}  "
          f"minor={review.convincing_minor_count})")
    print(f"  {'─'*50}\n")



def _extract_coverage_feedback(review: WriterReview) -> str:
    issue_list = []
    suggestion_list = []
    for sr in review.slide_reviews:
        cov = sr.criteria.get("coverage_and_clarity")
        if not cov:
            continue
        for issue in cov.convincing_critical_issues:
            issue_list.append(f"[Slide {sr.slide_index} '{sr.slide_title}']: {issue.description}")
            if issue.suggestion:
                suggestion_list.append(f"[Slide {sr.slide_index}]: {issue.suggestion}")

    feedback = {
        "issue_list": issue_list,
        "suggestion": suggestion_list,
    }
    return json.dumps(feedback, ensure_ascii=False, indent=2)


def create_workflow() -> StateGraph:
    workflow     = StateGraph(WorkflowState)
    planner      = PlannerAgent(Config.LLM_MODEL_NAME)
    writer       = WriterAgent(Config.LLM_MODEL_NAME)
    reviewer     = ReviewerAgent(Config.LLM_MODEL_NAME)
    refiner      = WriterRefinerAgent(Config.LLM_MODEL_NAME)
    plan_specer  = PlanSpecerAgent(Config.LLM_MODEL_NAME)


    def planner_node(state: WorkflowState) -> Dict[str, Any]:
        feedback_str = state.get("coverage_feedback")
        if feedback_str:
            print(f"\n{'='*60}")
            print(f" Planner — Re-generating outline with coverage feedback...")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f" Planner — Generating initial outline...")
            print(f"{'='*60}\n")

        plan = planner.create_outline(state["document_context"], feedback=feedback_str)

        lecture_title = planner.generate_title(plan["outline"])
        print(f"\nGenerated lecture title: {lecture_title}\n")

        return {
            "lecture_plan":        plan,
            "lecture_title":       lecture_title,
            "current_section_idx": 0,
            "slides":              [],
            "current_iteration":   0,
        }

    def plan_specer_node(state: WorkflowState) -> Dict[str, Any]:
        outline_md = state["lecture_plan"]["outline"]
        print(f"\n{'='*60}")
        print(f" Plan Specer — Specifying slide specs from outline...")
        print(f"{'='*60}\n")
        specs = plan_specer.specify(outline_md, state["document_context"])
        return {"slide_specs": specs}

    def writer_node(state: WorkflowState) -> Dict[str, Any]:
        slide_specs = state.get("slide_specs", [])
        print(f"  Writer — drafting {len(slide_specs)} slide(s) in one batch call...")
        slides = writer.draft_slides(
            slide_specs=slide_specs,
            context=state["document_context"],
        )
        return {
            "slides":              slides,
            "current_section_idx": len(slides),
        }

    async def reviewer_node(state: WorkflowState) -> Dict[str, Any]:
        review = await reviewer.evaluate(
            state["slides"],
            state["document_context"],
            state["lecture_plan"],
            slide_specs=state.get("slide_specs", []),
        )
        write_iter = state.get("current_iteration", 0)
        _print_writer_review(f"Writer Reviewer (iteration {write_iter})", review)

        current_best_score = state.get("best_slides_score", float("inf"))
        n_critical = review.convincing_critical_count

        if n_critical < current_best_score:
            print(f"New best slides!  {n_critical} critical issues (was {current_best_score})")
            return {
                "reviewer_feedback":   review,
                "best_slides":         state["slides"],
                "best_slides_score":   float(n_critical),
                "best_slides_feedback": review,
            }

        return {"reviewer_feedback": review}

    def should_continue(state: WorkflowState) -> str:
        review = state.get("reviewer_feedback")
        if not review:
            return "end"

        if review.passed:
            return "end"

        current_iter = state.get("current_iteration", 0)
        if current_iter < Config.FEEDBACK_INTERATION_NUMBER:
            return "retry"

        n_critical = review.convincing_critical_count
        n_major    = review.convincing_major_count
        n_minor    = review.convincing_minor_count
        backtrack_used = state.get("planner_backtrack_used", False)

        if (
            not backtrack_used
            and n_critical > Config.BACK_PLANNER_CRITICAL_NUM
            and n_major    > Config.BACK_PLANNER_MAJOR_NUM
            and n_minor    > Config.BACK_PLANNER_MINOR_NUM
        ):
            print(
                f"\nBacktrack threshold reached after {current_iter} iterations: "
                f"critical={n_critical} (>{Config.BACK_PLANNER_CRITICAL_NUM})  "
                f"major={n_major} (>{Config.BACK_PLANNER_MAJOR_NUM})  "
                f"minor={n_minor} (>{Config.BACK_PLANNER_MINOR_NUM})"
            )
            print("Backtracking to planner (1-time only)...\n")
            return "backtrack_planner"

        return "end"

    def increment_iteration(state: WorkflowState) -> Dict[str, Any]:
        new_iter = state.get("current_iteration", 0) + 1
        print(f"\n{'='*60}")
        print(f" Writer iteration {new_iter}/3 — Refining failed slides...")
        print(f"{'='*60}\n")
        return {"current_iteration": new_iter}

    def writer_refiner_node(state: WorkflowState) -> Dict[str, Any]:
        review: WriterReview = state["reviewer_feedback"]
        outline_md = state["lecture_plan"]["outline"]

        refined_slides = refiner.refine(
            slides=list(state["slides"]),
            writer_review=review,
            context=state["document_context"],
            slide_specs=state.get("slide_specs", []),
        )
        return {"slides": refined_slides}

    def backtrack_to_planner_node(state: WorkflowState) -> Dict[str, Any]:
        review: WriterReview = state["reviewer_feedback"]
        feedback_json = _extract_coverage_feedback(review)

        print(f"\n{'='*60}")
        print(f" Backtrack — Sending coverage feedback to planner:")
        print(feedback_json[:500])
        print(f"{'='*60}\n")

        return {
            "coverage_feedback":      feedback_json,
            "planner_backtrack_used": True,
            "current_iteration":      0,
            "best_slides":            None,
            "best_slides_score":      float("inf"),
            "best_slides_feedback":   None,
        }

    def finalize_slides_node(state: WorkflowState) -> Dict[str, Any]:
        best = state.get("best_slides")
        if best:
            n_iter = state.get("current_iteration", 0)
            print(f"\nUsing best slides (tracked across {n_iter} writer iteration(s))")
            return {"slides": best}
        return {}

    workflow.add_node("planner",              planner_node)
    workflow.add_node("plan_specer",          plan_specer_node)
    workflow.add_node("writer",               writer_node)
    workflow.add_node("reviewer",             reviewer_node)
    workflow.add_node("increment",            increment_iteration)
    workflow.add_node("writer_refiner",       writer_refiner_node)
    workflow.add_node("backtrack_to_planner", backtrack_to_planner_node)
    workflow.add_node("finalize_slides",      finalize_slides_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner",     "plan_specer")
    workflow.add_edge("plan_specer", "writer")
    workflow.add_edge("writer",      "reviewer")

    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "retry":              "increment",
            "backtrack_planner":  "backtrack_to_planner",
            "end":                "finalize_slides",
        },
    )

    workflow.add_edge("increment",       "writer_refiner")
    workflow.add_edge("writer_refiner",  "reviewer")
    workflow.add_edge("backtrack_to_planner", "planner")
    workflow.add_edge("finalize_slides", END)

    return workflow.compile()
