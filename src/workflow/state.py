from typing import TypedDict, List, Dict, Any, Optional
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.models.feedback import WriterReview


class WorkflowState(TypedDict):
    document_context:          DocumentContext
    lecture_plan:              Dict[str, Any]
    lecture_title:             str
    slides:                    List[SlideContent]
    current_iteration:         int
    reviewer_feedback:         Optional[WriterReview]
    best_slides:               Optional[List[SlideContent]]
    best_slides_score:         float
    best_slides_feedback:      Optional[WriterReview]
    slide_specs:               Optional[List[Slide]]
    planner_backtrack_used:    bool
    coverage_feedback:         Optional[str]
