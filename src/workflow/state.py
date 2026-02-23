from typing import TypedDict, List, Dict, Any, Optional
from src.models.context import DocumentContext
from src.models.slide import SlideContent, ReviewerFeedback

class WorkflowState(TypedDict):
    document_context: DocumentContext
    lecture_plan: Dict[str, Any]
    slides: List[SlideContent]
    current_section_idx: int
    current_iteration: int
    reviewer_feedback: Optional[ReviewerFeedback]
    rubric_scores: Optional[Dict[str, Any]]

