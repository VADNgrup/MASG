import asyncio
from src.utils.llm import chat, achat
from typing import List, Dict, Any
import json
from dataclasses import asdict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.models.feedback import Issue, CriterionResult, SlideReview, WriterReview, Severity
from src.ingestion.vector_store import VectorStoreManager

class ReviewerAgent:

    def __init__(self, model: str):
        self.model = model

    async def evaluate(self, slides: List[SlideContent], context: DocumentContext, lecture_plan: Dict[str, Any], slide_specs: List[Slide]=None) -> WriterReview:
        (faith_reviews, cov_reviews, pres_reviews, coh_reviews) = await asyncio.gather(
            self._evaluate_faithfulness(slides, context),
            self._evaluate_coverage_and_clarity(slides, lecture_plan, slide_specs or []),
            self._evaluate_presentation_quality(slides, lecture_plan),
            self._evaluate_coherence(slides)
        )
        merged: Dict[int, SlideReview] = {}
        for (idx, slide) in enumerate(slides, 1):
            merged[idx] = SlideReview(slide_index=idx, slide_title=slide.slide.slide_title, criteria={})
        for (criterion_name, reviews) in [('faithfulness', faith_reviews), ('coverage_and_clarity', cov_reviews), ('presentation_quality', pres_reviews), ('coherence', coh_reviews)]:
            for sr in reviews:
                if sr.slide_index in merged:
                    merged[sr.slide_index].criteria[criterion_name] = sr.criteria.get(criterion_name, CriterionResult(criterion=criterion_name))
            for slide_idx in merged:
                if criterion_name not in merged[slide_idx].criteria:
                    merged[slide_idx].criteria[criterion_name] = CriterionResult(criterion=criterion_name, issues=[])
        return WriterReview(slide_reviews=list(merged.values()))

    async def _evaluate_faithfulness(self, slides: List[SlideContent], context: DocumentContext) -> List[SlideReview]:
        slides_json = json.dumps(
            [{'slide_number': i, 'slide_title': s.slide.slide_title, 'content': s.content} for (i, s) in enumerate(slides, 1)],
            indent=2
        )
        try:
            vsm = VectorStoreManager(context.document_id)
            vectorstore = vsm.load_vector_store()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            combined_context = []
            for s in slides:
                query = f"{s.slide.slide_title}: {s.content}"
                docs = await retriever.ainvoke(query)
                combined_context.append(
                    f"--- Source Context for Slide {s.slide.slide_number}: '{s.slide.slide_title}' ---\n"
                    + "\n".join([d.page_content for d in docs])
                )
            reference_text = "\n\n".join(combined_context)
        except Exception as e:
            print(f"Warning: RAG retrieval failed in reviewer ({e}), falling back to truncation.")
            reference_text = context.text_content.markdown[:10000]

        prompt = (
            "You are a fact-checker reviewing lecture slide DRAFTS (written as paragraphs, not yet formatted as bullets).\n"
            "Compare each slide's content against the retrieved source document context.\n"
            "Flag ONLY clear, near-certain factual errors — NOT style, tone, or paraphrasing.\n\n"
            f"SOURCE DOCUMENT CONTEXTS:\n{reference_text}\n\n"
            f"SLIDES (draft paragraphs):\n{slides_json}\n\n"
            "# WHAT TO FLAG (only if confidence > 0.92):\n"
            "- A specific fact, number, name, or year that directly contradicts the source\n"
            "  (e.g., source says 1947 but slide says 1974)\n"
            "- A claim that is completely absent from all source contexts and cannot be inferred (hallucination)\n\n"
            "# WHAT NOT TO FLAG:\n"
            "- Paraphrasing or rewording that preserves the correct meaning\n"
            "- Information the source implies but does not state verbatim\n"
            "- Missing details that are not factually wrong\n"
            "- Style, tone, or length differences\n\n"
            "Slides with no issues should NOT appear. Return ONLY valid JSON:\n"
            '{\n  "slide_reviews": [\n    {\n      "slide_number": 3,\n      "issues": [\n        {\n'
            '          "severity": "critical",\n'
            '          "location": "Slide 3",\n'
            '          "description": "Slide states algorithm was invented in 1974, but source clearly states 1947",\n'
            '          "suggestion": "Correct the year to 1947 as stated in the source",\n'
            '          "confidence_score": 0.96\n'
            '        }\n      ]\n    }\n  ]\n}'
        )
        content = await achat(self.model, [{'role': 'user', 'content': prompt}], temperature=0.1)
        return self._parse_slide_reviews('faithfulness', content, slides)

    async def _evaluate_coverage_and_clarity(self, slides: List[SlideContent], lecture_plan: Dict[str, Any], slide_specs: List[Slide]) -> List[SlideReview]:
        slides_json = json.dumps(
            [{'slide_number': i, 'slide_title': s.slide.slide_title, 'content': s.content} for (i, s) in enumerate(slides, 1)],
            indent=2
        )
        specs_json = json.dumps(
            [{'slide_number': i, 'slide_title': spec.slide_title, 'goal': spec.goal} for (i, spec) in enumerate(slide_specs, 1)],
            indent=2, ensure_ascii=False
        ) if slide_specs else '(no specs provided)'

        prompt = (
            "You are a curriculum reviewer. Each slide has an explicit GOAL it must achieve.\n"
            "Your job: verify the slide draft actually covers what the goal requires.\n\n"
            f"SLIDE SPECIFICATIONS (goal each slide MUST fulfil):\n{specs_json}\n\n"
            f"SLIDES (draft paragraphs — not yet formatted as bullet points):\n{slides_json}\n\n"
            "# EVALUATION: GOAL COVERAGE ONLY\n"
            "For each slide, ask:\n"
            "1. Does the content address the core idea stated in the goal?\n"
            "2. Is there a KEY concept from the goal that is COMPLETELY absent (not just briefly mentioned)?\n"
            "3. Does the content drift entirely off-topic from the goal?\n\n"
            "# DO NOT FLAG:\n"
            "- Paragraph format vs bullet points (Formatter will convert this)\n"
            "- Writing style or tone\n"
            "- A concept mentioned briefly — only flag if COMPLETELY missing\n"
            "- Depth of explanation unless the goal explicitly requires deep detail\n\n"
            "Slides with no issues should NOT appear. Return ONLY valid JSON:\n"
            '{\n  "slide_reviews": [\n    {\n      "slide_number": 5,\n      "issues": [\n        {\n'
            '          "severity": "critical",\n'
            '          "location": "Slide 5",\n'
            '          "description": "Goal requires explaining the constraint formulation but slide has no mention of constraints at all",\n'
            '          "suggestion": "Include the constraint equations or describe what they represent",\n'
            '          "confidence_score": 0.93\n'
            '        }\n      ]\n    }\n  ]\n}\n'
            "Severity guide:\n"
            "- 'critical': a KEY part of the goal is completely absent — confidence > 0.90\n"
            "- 'major': goal partially met but an important supporting idea is missing — confidence > 0.85\n"
            "- 'minor': a small clarification would better serve the goal — confidence > 0.80\n"
            "Omit any issue below its confidence threshold."
        )
        content = await achat(self.model, [{'role': 'user', 'content': prompt}], temperature=0.2)
        return self._parse_slide_reviews('coverage_and_clarity', content, slides)

    async def _evaluate_presentation_quality(self, slides: List[SlideContent], lecture_plan: Dict[str, Any]) -> List[SlideReview]:
        slides_json = json.dumps(
            [{'slide_number': i, 'slide_title': s.slide.slide_title, 'content': s.content} for (i, s) in enumerate(slides, 1)],
            indent=2
        )
        prompt = (
            "You are reviewing lecture slide DRAFTS written as prose paragraphs (not yet formatted as bullet points).\n"
            "Focus ONLY on whether each slide teaches its topic clearly and substantively.\n\n"
            f"SLIDES:\n{slides_json}\n\n"
            "# WHAT TO EVALUATE\n"
            "1. SUBSTANCE: Does the slide contain real educational content, or is it vague filler?\n"
            "   - Flag if a slide is essentially empty (only 1 vague sentence with no actual information)\n"
            "   - Flag if content is entirely generic (e.g., 'LP is important and useful' with nothing else)\n\n"
            "2. TITLE-CONTENT MATCH: Does the content actually match what the title promises?\n"
            "   - Flag if title says 'Product Mix Problem Setup' but content talks about something unrelated\n\n"
            "# DO NOT FLAG:\n"
            "- Paragraph format vs bullet points (Formatter converts this)\n"
            "- Word count or number of sentences\n"
            "- Academic tone or formal writing style\n"
            "- Math-heavy slides being longer than average (math requires more text)\n\n"
            "Slides with no issues should NOT appear. Return ONLY valid JSON:\n"
            '{\n  "slide_reviews": [\n    {\n      "slide_number": 2,\n      "issues": [\n        {\n'
            '          "severity": "major",\n'
            '          "location": "Slide 2",\n'
            '          "description": "Content is entirely generic with no specific facts, dates, or mechanisms from source material",\n'
            '          "suggestion": "Add at least one concrete fact or example from the source",\n'
            '          "confidence_score": 0.88\n'
            '        }\n      ]\n    }\n  ]\n}\n'
            "Severity guide:\n"
            "- 'major': slide is essentially empty or completely off-topic from its title — confidence > 0.85\n"
            "- 'minor': slide is thin but has some useful content — confidence > 0.80\n"
            "Omit any issue below its confidence threshold."
        )
        content = await achat(self.model, [{'role': 'user', 'content': prompt}], temperature=0.2)
        return self._parse_slide_reviews('presentation_quality', content, slides)

    async def _evaluate_coherence(self, slides: List[SlideContent]) -> List[SlideReview]:
        slides_json = json.dumps(
            [{'slide_number': i, 'slide_title': s.slide.slide_title, 'content': s.content} for (i, s) in enumerate(slides, 1)],
            indent=2
        )
        prompt = (
            "You are checking whether lecture slide drafts flow logically from one to the next.\n\n"
            f"SLIDES:\n{slides_json}\n\n"
            "# WHAT TO CHECK\n"
            "Only flag if a slide has an EXTREME, disorienting topic jump that would confuse a student.\n"
            "Example: jumping from 'History of LP' directly into 'Software UI walkthrough' with absolutely no bridge.\n\n"
            "# DO NOT FLAG:\n"
            "- Normal section transitions (e.g., Introduction → Model Formulation is expected)\n"
            "- Slight thematic shifts within the same topic area\n"
            "- Mathematical content following conceptual content (normal in STEM lectures)\n"
            "- Sub-topic progression within the same main section\n\n"
            "Return ONLY valid JSON listing only slides WITH issues (most slides will have none):\n"
            '{\n  "slide_reviews": [\n    {\n      "slide_number": 4,\n      "issues": [\n        {\n'
            '          "severity": "major",\n'
            '          "location": "Slide 4",\n'
            '          "description": "Slide 3 ends on model constraints; Slide 4 opens on software UI with no bridge",\n'
            '          "suggestion": "Add a sentence connecting model formulation to its software implementation",\n'
            '          "confidence_score": 0.87\n'
            '        }\n      ]\n    }\n  ]\n}\n'
            "Severity:\n"
            "- 'major': truly disorienting jump that breaks student comprehension — confidence > 0.85\n"
            "- 'minor': slight thematic shift that could benefit from a bridging phrase — confidence > 0.80\n"
            "Omit any issue below its confidence threshold."
        )
        content = await achat(self.model, [{'role': 'user', 'content': prompt}], temperature=0.2)
        return self._parse_slide_reviews('coherence', content, slides)

    def _parse_slide_reviews(self, criterion_name: str, content: str, slides: List[SlideContent]) -> List[SlideReview]:
        try:
            data = json.loads(content)
        except Exception:
            clean = content.strip()
            if clean.startswith('```json'):
                clean = clean.split('```json')[1].split('```')[0]
            elif clean.startswith('```'):
                clean = clean.split('```')[1].split('```')[0]
            try:
                data = json.loads(clean.strip())
            except Exception:
                return []
        valid_indices = set(range(1, len(slides) + 1))
        result: List[SlideReview] = []
        for entry in data.get('slide_reviews', []):
            if not isinstance(entry, dict):
                continue
            slide_number = int(entry.get('slide_number', -1))
            if slide_number not in valid_indices:
                continue
            slide = slides[slide_number - 1]
            issues: List[Issue] = []
            for item in entry.get('issues', []):
                if not isinstance(item, dict):
                    continue
                try:
                    severity = Severity(item.get('severity', 'minor').lower())
                except ValueError:
                    severity = Severity.MINOR
                issues.append(Issue(
                    severity=severity,
                    location=str(item.get('location', f'Slide {slide_number}')),
                    description=str(item.get('description', '')),
                    suggestion=str(item.get('suggestion', '')),
                    confidence_score=float(item.get('confidence_score', 0.0))
                ))
            result.append(SlideReview(
                slide_index=slide_number,
                slide_title=slide.slide.slide_title,
                criteria={criterion_name: CriterionResult(criterion=criterion_name, issues=issues)}
            ))
        return result