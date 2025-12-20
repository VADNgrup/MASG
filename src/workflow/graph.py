from langgraph.graph import StateGraph, END
from typing import Dict, Any
import uuid
from src.workflow.state import WorkflowState
from src.workflow.agents.planner import PlannerAgent
from src.workflow.agents.writer import WriterAgent
from src.workflow.agents.asset_manager import AssetManager
from src.workflow.agents.reviewer import ReviewerAgent
from src.workflow.agents.refiner import SlideRefinerAgent
from src.workflow.agents.coverage_checker import ContentCoverageChecker
from src.optimization.reward_function import compute_and_emit_reward
from src.optimization.lightning_manager import lightning_manager

def create_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)
    
    planner = PlannerAgent()
    writer = WriterAgent()
    asset_manager = AssetManager()
    reviewer = ReviewerAgent()
    refiner = SlideRefinerAgent()
    coverage_checker = ContentCoverageChecker()
    
    def planner_node(state: WorkflowState) -> Dict[str, Any]:
        plan = planner.create_outline(state["document_context"])
        return {
            "lecture_plan": plan,
            "current_section_idx": 0,
            "slides": [],
            "image_decisions": []
        }
    
    def writer_node(state: WorkflowState) -> Dict[str, Any]:
        sections = state["lecture_plan"]["sections"]
        slides = state["slides"].copy() if state["slides"] else []
        
        feedback = None
        if state.get("reviewer_feedback"):
            feedback = state["reviewer_feedback"].summary
        
        for section in sections:
            slide = writer.draft_slide(section, state["document_context"], feedback)
            slides.append(slide)
        
        return {
            "slides": slides,
            "current_section_idx": len(sections)
        }
    
    async def asset_manager_node(state: WorkflowState) -> Dict[str, Any]:
        slides = state["slides"]
        image_decisions = state.get("image_decisions", []).copy()
        
        for slide in slides:
            if not slide.image_query or slide.image:
                continue
            
            image_ref, decision_log = await asset_manager.resolve_image(
                slide.image_query,
                state["document_context"],
                slide_title=slide.title,
                slide_content=slide.content
            )
            
            slide.image = image_ref
            image_decisions.append(decision_log)
        
        return {"image_decisions": image_decisions}
    
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
            "rubric_scores": feedback.criteria,
            "optimization_hints": {"coverage": coverage}
        }
    
    def optimization_node(state: WorkflowState) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        
        rubric_scores = state.get("rubric_scores", {})
        optimization_hints = state.get("optimization_hints", {})
        coverage_metrics = optimization_hints.get("coverage", {})
        
        if rubric_scores:
            compute_and_emit_reward(rubric_scores, coverage_metrics, task_id)
            lightning_manager.increment_trace_count()
            
            if lightning_manager.should_train():
                lightning_manager.train()
        
        return {}
    
    def should_continue(state: WorkflowState) -> str:
        if state["current_iteration"] >= 3:
            return "end"
        
        if not state.get("reviewer_feedback"):
            return "review"
        
        decision = state["reviewer_feedback"].decision
        
        if decision == "ACCEPT":
            return "end"
        elif decision == "RETRY" and state["current_iteration"] < 3:
            return "retry"
        else:
            return "end"
    
    def increment_iteration(state: WorkflowState) -> Dict[str, Any]:
        return {
            "current_iteration": state["current_iteration"] + 1,
            "current_section_idx": 0,
            "slides": []
        }
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("asset_manager", asset_manager_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("increment", increment_iteration)
    
    def should_continue_writing(state: WorkflowState) -> str:
        sections = state["lecture_plan"]["sections"]
        current_idx = state["current_section_idx"]
        
        if current_idx >= len(sections):
            return "done_writing"
        else:
            return "continue_writing"
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "writer")
    workflow.add_edge("writer", "asset_manager")
    workflow.add_edge("asset_manager", "reviewer")
    workflow.add_edge("reviewer", "optimization")
    
    workflow.add_conditional_edges(
        "optimization",
        should_continue,
        {
            "review": "reviewer",
            "retry": "increment",
            "end": END
        }
    )
    
    workflow.add_edge("increment", "writer")
    
    return workflow.compile()

