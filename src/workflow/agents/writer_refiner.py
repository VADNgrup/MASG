from typing import List, Optional
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.models.feedback import WriterReview, SlideReview, Issue
from src.workflow.agents.writer import WriterAgent


def _build_slide_feedback(slide_review: SlideReview) -> str:
    """Build a feedback string from all issues that passed their per-severity
    confidence threshold (CRITICAL > 0.9, MAJOR > 0.85, MINOR > 0.8).
    Ordered by severity so the writer addresses the most important issues first.
    """
    severity_order = {"critical": 0, "major": 1, "minor": 2}
    issues: List[Issue] = sorted(
        slide_review.convincing_issues,
        key=lambda i: severity_order.get(i.severity.value, 99),
    )
    if not issues:
        return ""

    lines = ["The following issues were found in this slide and must be addressed:"]
    for i, issue in enumerate(issues, 1):
        lines.append(
            f"  {i}. [{issue.severity.value.upper()}] {issue.location}: "
            f"{issue.description} → Suggestion: {issue.suggestion}"
        )
    return "\n".join(lines)


class WriterRefinerAgent:
    def __init__(self, model: str):
        self.writer = WriterAgent(model)

    def refine(
        self,
        slides: List[SlideContent],
        writer_review: WriterReview,
        context: DocumentContext,
        slide_specs: List[Slide] = None,
    ) -> List[SlideContent]:
        failed_slides: List[SlideReview] = writer_review.failed_slides

        if not failed_slides:
            return slides

        slides_by_index = {i: s for i, s in enumerate(slides, 1)}

        specs_by_title = {}
        if slide_specs:
            for spec in slide_specs:
                specs_by_title[spec.slide_title.lower()] = spec

        print(
            f"\nWriter Refiner: fixing {len(failed_slides)} failed slide(s): "
            f"{[sr.slide_index for sr in failed_slides]}"
        )

        batch_input: List[tuple] = []
        for slide_review in failed_slides:
            slide_idx = slide_review.slide_index
            original_slide = slides_by_index.get(slide_idx)
            if original_slide is None:
                continue

            slide_title = original_slide.slide.slide_title
            spec = specs_by_title.get(slide_title.lower(), original_slide.slide)
            feedback_str = _build_slide_feedback(slide_review)

            print(f"    Queued slide {slide_idx}: '{slide_title}'")
            batch_input.append((slide_idx, spec, feedback_str if feedback_str else None))

        if not batch_input:
            return slides

        refined_slides = self.writer.draft_slides_with_feedback(
            slide_specs_with_feedback=batch_input,
            context=context,
        )

        for (orig_idx, _, _), refined_slide in zip(batch_input, refined_slides):
            slides_by_index[orig_idx] = refined_slide

        return [slides_by_index[i] for i in sorted(slides_by_index.keys())]
