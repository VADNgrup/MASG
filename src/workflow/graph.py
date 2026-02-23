from langgraph.graph import StateGraph, END
from typing import Dict, Any
from src.workflow.state import WorkflowState
from src.workflow.agents.planner import PlannerAgent
from src.workflow.agents.writer import WriterAgent
from src.workflow.agents.reviewer import ReviewerAgent
from src.workflow.agents.coverage_checker import ContentCoverageChecker

def create_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)
    
    planner = PlannerAgent()
    writer = WriterAgent()
    reviewer = ReviewerAgent()
    coverage_checker = ContentCoverageChecker()
    
    def planner_node(state: WorkflowState) -> Dict[str, Any]:
        plan = planner.create_outline(state["document_context"])
        return {
            "lecture_plan": plan,
            "current_section_idx": 0,
            "slides": []
        }
    
    def writer_node(state: WorkflowState) -> Dict[str, Any]:
        outline_md = state["lecture_plan"]["outline"]
        
        feedback = None
        if state.get("reviewer_feedback"):
            feedback = state["reviewer_feedback"].summary
        
        slides = writer.draft_slide_from_outline(
            outline_md,
            state["document_context"],
            feedback
        )
        
        return {
            "slides": slides,
            "current_section_idx": len(slides)
        }
    
    async def reviewer_node(state: WorkflowState) -> Dict[str, Any]:
        coverage = coverage_checker.check_coverage(
            state["document_context"].text_content.markdown,
            state["slides"]
        )
        
        feedback = await reviewer.evaluate(
            state["slides"],
            state["document_context"],
            state["lecture_plan"]
        )
        
        if coverage["coverage_percent"] < 70 and state["current_iteration"] < 2:
            feedback.decision = "RETRY"
            feedback.summary += f" Coverage only {coverage['coverage_percent']:.1f}%. Missing: {', '.join(coverage['missing_content'][:3])}"
        
        return {
            "reviewer_feedback": feedback,
            "rubric_scores": feedback.criteria
        }
    
    def should_continue(state: WorkflowState) -> str:
        if state["current_iteration"] >= 3:
            return "end"
        
        feedback = state.get("reviewer_feedback")
        if not feedback:
            return "end"
        
        decision = feedback.decision
        
        if decision == "ACCEPT":
            return "end"
        elif decision == "RETRY" and state["current_iteration"] < 3:
            return "retry"
        else:
            return "end"
    
    def increment_iteration(state: WorkflowState) -> Dict[str, Any]:
        new_iteration = state["current_iteration"] + 1
        print(f"\n{'='*60}")
        print(f"🔄 Iteration {new_iteration}/3 - Retrying with feedback...")
        print(f"{'='*60}\n")
        return {
            "current_iteration": new_iteration,
            "current_section_idx": 0,
            "slides": []
        }
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("increment", increment_iteration)
    

    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "writer")
    workflow.add_edge("writer", "reviewer")
    
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "retry": "increment",
            "end": END
        }
    )
    
    workflow.add_edge("increment", "writer")
    
    return workflow.compile()

