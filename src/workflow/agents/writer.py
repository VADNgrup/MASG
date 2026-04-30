from src.utils.llm import chat
from typing import Dict, Optional, List
import json
from src.utils.parse_llm_response import parse_json_response
from dataclasses import asdict
from src.models.context import DocumentContext
from src.models.slide import SlideContent, Slide
from src.ingestion.vector_store import VectorStoreManager

class WriterAgent:

    def __init__(self, model: str):
        self.model = model

    def _chat(self, messages: list, temperature: float=0.4, max_tokens: int=None) -> str:
        return chat(self.model, messages, temperature=temperature, max_tokens=max_tokens)

    def _retrieve_relevant_text(self, context: DocumentContext, slide_specs: List[Slide]) -> str:
        try:
            vsm = VectorStoreManager(context.document_id)
            vectorstore = vsm.load_vector_store()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            
            combined_context = []
            for spec in slide_specs:
                query = f"{spec.slide_title}: {spec.goal}"
                docs = retriever.invoke(query)
                combined_context.append(f"--- Context for '{spec.slide_title}' ---\n" + "\n".join([d.page_content for d in docs]))
            
            return "\n\n".join(combined_context)
        except Exception as e:
            print(f"Warning: RAG retrieval failed ({e}), falling back to truncation.")
            full_text = context.text_content.markdown
            return full_text if len(full_text) <= 12000 else full_text[:12000]

    def _build_batch_system_prompt(self) -> str:
        return '''# ROLE
You are an expert lecture writer specializing in highly accurate and detailed academic material.

# TASK
You will receive a list of slide specifications and the relevant source material from the Vector DB.
Generate content for ALL slides at once in a single response.

# CORE PRINCIPLE
All generated content must satisfy two quality criteria:
- Faithfulness: Each slide must accurately reflect the meaning, tone, and technical content of the source material. DO NOT ADD INFO outside the source.
- Coverage: Together, all slides should cover the key ideas, arguments, and details present in the source material according to the slide goal.

# SLIDE CONSTRUCTION RULES
- Stay strictly within the scope of each slide's description / goal.
- Draft the content as FULL, COMPREHENSIVE PARAGRAPHS. DO NOT USE BULLET POINTS yet.
- Ensure absolutely nothing important is missed from the source chunks. Write in a descriptive, educational tone.
- Emphasize logical transitions (cause-and-effect) and coherence.
- Use proper LaTeX for any mathematical expression.

# PRESERVE SPECIFIC DETAILS (CRITICAL)
- ALWAYS preserve specific names: people, companies, software, tools, brands, institutions.
  Example: If source mentions "BIOVIA, labguru, labfolder, RSpace, eLABJOURNAL", ALL of these must appear in the relevant slide.
- ALWAYS preserve specific numbers: years, statistics, measurements, percentages.
- NEVER generalize away concrete details. "Several software tools exist" is WRONG if the source names them.
- If the source provides a list of items, include ALL items — do not summarize as "etc." or "and others".

# MATHEMATICS & NOTATION
- Inline mathematical expressions are wrapped in LaTeX delimiters by using $...$
- CRITICAL: For multiline LaTeX equations, use double-backslash `\\\\` for newlines. 
- NEVER use the character `\n` (newline) inside a LaTeX string in the JSON output. 
- Keep all LaTeX clean and valid.

# OUTPUT FORMAT
Return ONLY valid JSON — an array with one object per slide, in the same order as the input specifications:
[
  {
    "slide_number": 1,
    "content": "A comprehensive paragraph fully covering the topic and goal of the slide based on the source text..."
  },
  {
    "slide_number": 2,
    "content": "Detailed paragraphs..."
  }
]
'''

    def draft_slides(self, slide_specs: List[Slide], context: DocumentContext) -> List[SlideContent]:
        text_excerpt = self._retrieve_relevant_text(context, slide_specs)
        specs_payload = []
        for (i, spec) in enumerate(slide_specs, 1):
            d = asdict(spec)
            if hasattr(d.get('slide_type'), 'value'):
                d['slide_type'] = d['slide_type'].value
            else:
                d['slide_type'] = str(d.get('slide_type', ''))
            d['slide_number'] = i
            specs_payload.append(d)
        user_prompt = f'SOURCE MATERIAL:\n{text_excerpt}\n\nSLIDE SPECIFICATIONS:\n{json.dumps(specs_payload, ensure_ascii=False, indent=2)}'
        raw = self._chat([{'role': 'system', 'content': self._build_batch_system_prompt()}, {'role': 'user', 'content': user_prompt}], temperature=0.4, max_tokens=16000)
        return self._parse_batch_response(raw, slide_specs)

    def draft_slides_with_feedback(self, slide_specs_with_feedback: List[tuple], context: DocumentContext) -> List[SlideContent]:
        slide_specs_ordered = [spec for (_, spec, _) in slide_specs_with_feedback]
        text_excerpt = self._retrieve_relevant_text(context, slide_specs_ordered)
        specs_payload = []
        slide_specs_ordered: List[Slide] = []
        for (seq_num, (orig_idx, spec, feedback)) in enumerate(slide_specs_with_feedback, 1):
            d = asdict(spec)
            if hasattr(d.get('slide_type'), 'value'):
                d['slide_type'] = d['slide_type'].value
            else:
                d['slide_type'] = str(d.get('slide_type', ''))
            d['slide_number'] = seq_num
            if feedback:
                d['rewrite_feedback'] = feedback
            specs_payload.append(d)
            slide_specs_ordered.append(spec)
        user_prompt = f'SOURCE MATERIAL:\n{text_excerpt}\n\nSLIDE SPECIFICATIONS (with optional rewrite_feedback per slide):\n{json.dumps(specs_payload, ensure_ascii=False, indent=2)}'
        raw = self._chat([{'role': 'system', 'content': self._build_batch_system_prompt()}, {'role': 'user', 'content': user_prompt}], temperature=0.4, max_tokens=16000)
        return self._parse_batch_response(raw, slide_specs_ordered)

    def _parse_batch_response(self, raw: str, slide_specs: List[Slide]) -> List[SlideContent]:
        invoke_fn = lambda msgs: type('R', (), {'content': self._chat(msgs)})()
        data = parse_json_response(raw, invoke_fn, expect_list=True)
        by_number: Dict[int, object] = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    num = item.get('slide_number')
                    if num is not None:
                        by_number[int(num)] = item.get('content', [])
        results: List[SlideContent] = []
        for (i, spec) in enumerate(slide_specs, 1):
            content = by_number.get(i, [])
            results.append(SlideContent(slide=spec, content=content))
        return results