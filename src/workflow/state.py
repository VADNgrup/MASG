from typing import TypedDict, List, Dict, Any, Optional
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.models.feedback import WriterReview

class WorkflowState(TypedDict):
    document_context: DocumentContext
    lecture_plan: Dict[str, Any]
    lecture_title: str
    slides: List[SlideContent]
    reviewer_feedback: Optional[WriterReview]
    slide_specs: Optional[List[Slide]]