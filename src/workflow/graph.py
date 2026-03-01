from langgraph.graph import StateGraph, END
from typing import Dict, Any
from src.workflow.state import WorkflowState
from src.workflow.agents.planner import PlannerAgent
from src.workflow.agents.writer import WriterAgent
from src.workflow.agents.writer_reviewer import ReviewerAgent
from src.workflow.agents.planner_reviewer import PlannerReviewerAgent


def _build_feedback_string(fb) -> str:
    """Convert a ReviewerFeedback object into a structured text block for LLM prompts."""
    lines = [
        f"=== REVIEWER FEEDBACK (Overall: {fb.overall_score:.1f}/100 — {fb.decision}) ===",
        fb.summary,
        "",
    ]
    for criterion_name, criterion_score in fb.criteria.items():
        lines.append(f"[{criterion_name.upper()}]  Score: {criterion_score.score:.0f}/100")
        for issue in criterion_score.issues:
            lines.append(f"  ✗ {issue}")
        for suggestion in criterion_score.suggestions:
            lines.append(f"  → {suggestion}")
        lines.append("")
    return "\n".join(lines)


def _print_review_scores(label: str, fb) -> None:
    """Print per-criterion scores and weighted average for a reviewer pass."""
    weight = 1.0 / len(fb.criteria)          # equal weights (20% each for 5 criteria)
    weighted_avg = sum(c.score * weight for c in fb.criteria.values())
    print(f"\n  {'─'*50}")
    print(f"  {label} scores:")
    for name, criterion in fb.criteria.items():
        bar = '█' * int(criterion.score // 10) + '░' * (10 - int(criterion.score // 10))
        print(f"    {name:<22} {bar}  {criterion.score:5.1f}/100")
    print(f"  {'─'*50}")
    print(f"  Weighted Average (×{weight:.0%} each):   {weighted_avg:5.1f}/100  →  {fb.decision}")
    print(f"  {'─'*50}\n")


def create_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)
    planner          = PlannerAgent("qwen3-30b-a3b")
    planner_reviewer = PlannerReviewerAgent("qwen3.5-plus-2026-02-15")
    writer           = WriterAgent("qwen3-30b-a3b")
    reviewer         = ReviewerAgent("qwen3.5-plus-2026-02-15")

    # ------------------------------------------------------------------ #
    # PLANNER NODE                                                         #
    # ------------------------------------------------------------------ #
    def planner_node(state: WorkflowState) -> Dict[str, Any]:
        feedback = None
        if state.get("planner_reviewer_feedback"):
            feedback = _build_feedback_string(state["planner_reviewer_feedback"])

        plan = planner.create_outline(state["document_context"], feedback=feedback)
        return {
            "lecture_plan": plan,
            "current_section_idx": 0,
            "slides": [],
        }

    # ------------------------------------------------------------------ #
    # PLANNER REVIEWER NODE                                                #
    # ------------------------------------------------------------------ #
    async def planner_reviewer_node(state: WorkflowState) -> Dict[str, Any]:
        feedback = await planner_reviewer.evaluate(
            state["lecture_plan"],
            state["document_context"],
        )
        plan_iter = state.get("planner_iteration", 0)
        _print_review_scores(f"Planner Reviewer (plan iteration {plan_iter})", feedback)

        # Keep the best-scoring plan across all iterations
        current_best_score = state.get("best_plan_score", -1.0)
        if feedback.overall_score > current_best_score:
            print(f"  ★ New best plan!  {feedback.overall_score:.1f} > {current_best_score:.1f}")
            return {
                "planner_reviewer_feedback": feedback,
                "best_plan":        state["lecture_plan"],
                "best_plan_score":  feedback.overall_score,
            }

        return {
            "planner_reviewer_feedback": feedback,
        }

    def should_continue_planner(state: WorkflowState) -> str:
        if state.get("planner_iteration", 0) >= 3:
            return "write"

        feedback = state.get("planner_reviewer_feedback")
        if not feedback:
            return "write"

        if feedback.decision == "ACCEPT":
            return "write"
        elif feedback.decision == "RETRY" and state.get("planner_iteration", 0) < 3:
            return "retry_plan"
        else:
            return "write"

    def increment_planner_iteration(state: WorkflowState) -> Dict[str, Any]:
        new_iter = state.get("planner_iteration", 0) + 1
        print(f"\n{'='*60}")
        print(f"Planner iteration {new_iter}/3 — Revising outline...")
        print(f"{'='*60}\n")
        return {"planner_iteration": new_iter}

    # ------------------------------------------------------------------ #
    # WRITER NODE                                                          #
    # ------------------------------------------------------------------ #
    def writer_node(state: WorkflowState) -> Dict[str, Any]:
        outline_md = state["lecture_plan"]["outline"]

        feedback = None
        if state.get("reviewer_feedback"):
            feedback = _build_feedback_string(state["reviewer_feedback"])

        slides = writer.draft_slide_from_outline(
            outline_md,
            state["document_context"],
            feedback,
        )
        return {
            "slides": slides,
            "current_section_idx": len(slides),
        }

    # ------------------------------------------------------------------ #
    # WRITER REVIEWER NODE                                                 #
    # ------------------------------------------------------------------ #
    async def reviewer_node(state: WorkflowState) -> Dict[str, Any]:
        feedback = await reviewer.evaluate(
            state["slides"],
            state["document_context"],
            state["lecture_plan"],
        )
        write_iter = state.get("current_iteration", 0)
        _print_review_scores(f"Writer Reviewer (write iteration {write_iter})", feedback)

        # Keep the best-scoring slides across all iterations
        current_best_score = state.get("best_slides_score", -1.0)
        if feedback.overall_score > current_best_score:
            print(f"  ★ New best slides! {feedback.overall_score:.1f} > {current_best_score:.1f}")
            return {
                "reviewer_feedback":   feedback,
                "rubric_scores":       feedback.criteria,
                "best_slides":         state["slides"],
                "best_slides_score":   feedback.overall_score,
                "best_slides_feedback": feedback,
            }

        return {
            "reviewer_feedback": feedback,
            "rubric_scores":     feedback.criteria,
        }

    def should_continue(state: WorkflowState) -> str:
        if state.get("current_iteration", 0) >= 3:
            return "end"

        feedback = state.get("reviewer_feedback")
        if not feedback:
            return "end"

        if feedback.decision == "ACCEPT":
            return "end"
        elif feedback.decision == "RETRY" and state.get("current_iteration", 0) < 3:
            return "retry"
        else:
            return "end"

    def increment_iteration(state: WorkflowState) -> Dict[str, Any]:
        new_iter = state.get("current_iteration", 0) + 1
        print(f"\n{'='*60}")
        print(f" Writer iteration {new_iter}/3 — Retrying with feedback...")
        print(f"{'='*60}\n")
        return {
            "current_iteration": new_iter,
            "current_section_idx": 0,
            "slides": [],
        }

    # ------------------------------------------------------------------ #
    # WIRE UP THE GRAPH                                                    #
    # ------------------------------------------------------------------ #
    workflow.add_node("planner",          planner_node)
    workflow.add_node("planner_reviewer", planner_reviewer_node)
    workflow.add_node("increment_plan",   increment_planner_iteration)
    workflow.add_node("writer",           writer_node)
    workflow.add_node("reviewer",         reviewer_node)
    workflow.add_node("increment",        increment_iteration)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "planner_reviewer")

    workflow.add_conditional_edges(
        "planner_reviewer",
        should_continue_planner,
        {
            "retry_plan": "increment_plan",
            "write":      "writer",
        },
    )

    workflow.add_edge("increment_plan", "planner")
    workflow.add_edge("writer", "reviewer")

    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "retry": "increment",
            "end":   END,
        },
    )

    workflow.add_edge("increment", "writer")

    return workflow.compile()
