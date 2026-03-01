from typing import TypedDict, List, Dict, Any, Optional
from src.models.context import DocumentContext
from src.models.slide import SlideContent, ReviewerFeedback

class WorkflowState(TypedDict):
    document_context: DocumentContext
    lecture_plan: Dict[str, Any]
    slides: List[SlideContent]
    current_section_idx: int
    # Writer review loop
    current_iteration: int
    reviewer_feedback: Optional[ReviewerFeedback]
    rubric_scores: Optional[Dict[str, Any]]
    # Planner review loop
    planner_iteration: int
    planner_reviewer_feedback: Optional[ReviewerFeedback]
    # Best-effort tracking
    best_plan: Optional[Dict[str, Any]]
    best_plan_score: float
    best_slides: Optional[List[SlideContent]]
    best_slides_score: float
    best_slides_feedback: Optional[ReviewerFeedback]

