from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime

class ImageReference(BaseModel):
    source: Literal["original", "unsplash", "generated"]
    priority: int
    image_id: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    generation_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SlideContent(BaseModel):
    slide_id: str
    slide_type: str
    title: str
    content: List[str]
    speaker_notes: str
    image: Optional[ImageReference] = None
    image_query: Optional[str] = None

class LectureMetadata(BaseModel):
    source_document_id: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    total_slides: int
    quality_score: float
    iterations: int

class LectureOutput(BaseModel):
    lecture_id: str
    metadata: LectureMetadata
    slides: List[SlideContent]
    image_stats: Dict[str, int] = Field(default_factory=dict)
    decision_logs: List[Dict[str, Any]] = Field(default_factory=list)

class CriterionScore(BaseModel):
    score: float
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class ReviewerFeedback(BaseModel):
    overall_score: float
    decision: Literal["ACCEPT", "RETRY", "REJECT"]
    criteria: Dict[str, CriterionScore]
    specific_feedback: List[Dict[str, str]] = Field(default_factory=list)
    summary: str

