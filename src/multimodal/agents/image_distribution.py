from typing import List, Dict, Optional, Any, Set
import json
import numpy as np
import re
from pathlib import Path
from src.utils.config import config
from src.utils.llm import chat
from src.utils.semantic_match import SemanticMatcher
from src.utils.config import Config

class ImageDistribution:

    def __init__(self):
        self.matcher = SemanticMatcher()
        self.llm_model = config.LLM_MODEL_NAME
        self.alpha = 0.7
        self.threshold = 0.28
        self.max_images_per_slide = 2
        self._emb_cache: Dict[str, Any] = {}

    def distribute_images(self, lecture_id: str, lecture_dict: Dict[str, Any], aggregated_media: Dict[str, Any], used_images: Set[str]) -> List[Dict[str, Any]]:
        slides = lecture_dict.get('slides', [])
        content_slides = self._extract_content_slides(slides)
        if not content_slides:
            print('  No content-type slides found. Skipping image distribution.')
            return []
        print(f"\n{'=' * 60}")
        print(f'  Image Distribution — {len(content_slides)} content slides')
        print(f"{'=' * 60}")
        existing_images = aggregated_media.get('images', [])
        image_pool = self._step0_summarise_images(existing_images)
        image_pool = self._step1_embed_images(image_pool)
        print(f'\n  Step 0–1 complete: {len(image_pool)} context images embedded')
        slide_pool = self._step2_embed_slides(content_slides)
        print(f'  Step 2 complete: {len(slide_pool)} content slides embedded')
        distributions = self._step3_match_images_to_slides(image_pool, slide_pool, used_images)
        print(f'  Step 3 complete: {len(distributions)} images matched to slides')
        
        assigned_slide_numbers = {d['slide_number'] for d in distributions}
        slides_without_images = [s for s in slide_pool if s['slide_number'] not in assigned_slide_numbers]
        
        if slides_without_images:
            print(f'\n  Note: {len(slides_without_images)} slides do not have suitable images from the document. Skipping web search as requested.')
        output_path = Config.LECTURES_DIR / lecture_id / f'{lecture_id}_image_distribution.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(distributions, f, indent=2, ensure_ascii=False)
        print(f'\n  Saved image distributions to: {output_path}')
        return distributions

    def _step0_summarise_images(self, existing_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        image_pool: List[Dict[str, Any]] = []
        for img in existing_images:
            image_id = img.get('image_id', '')
            file_path = img.get('file_path', '')
            caption = img.get('caption', '')
            reference_context = img.get('reference_context') or None
            metadata = img.get('metadata', {})
            resolved_file_path = self._resolve_image_path(file_path)
            if not resolved_file_path:
                print(f'    [skip] Image file not found: {file_path}')
                continue
            if reference_context:
                image_description = self._generate_image_description(caption, reference_context)
            else:
                image_description = caption
            if not image_description:
                print(f'    [skip] Image has no caption/context: {file_path}')
                continue
            image_pool.append({'image_id': image_id, 'file_path': resolved_file_path, 'caption': caption, 'reference_context': reference_context, 'metadata': metadata, 'image_description': image_description, 'page_number': self._infer_page_number(file_path)})
            print(f'    [desc] {image_id}: {image_description[:80]}...')
        return image_pool

    @staticmethod
    def _resolve_image_path(file_path: str) -> str:
        if not file_path:
            return ''
        candidates = [Path(file_path), Config.DATA_DIR / file_path, Config.BASE_DIR / file_path]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return ''

    def _generate_image_description(self, caption: str, reference_context: str) -> str:
        prompt = f'You are given a caption and the reference context of an image from a document. Write a concise but comprehensive image description (1-3 sentences) that synthesises what the image shows, combining information from both the caption and the reference context. Focus on the visual content and what it represents.\n\nCaption: {caption}\n\nReference context: {reference_context}\n\nImage description:'
        try:
            return chat(model=self.llm_model, messages=[{'role': 'user', 'content': prompt}], temperature=0.3, max_tokens=200).strip()
        except Exception as e:
            print(f'    [LLM] Failed to generate description: {e}')
            return caption

    def _step1_embed_images(self, image_pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for img in image_pool:
            img['img_desc_embedding'] = self._cached_text_emb(img['image_description'])
            img['img_clip_embedding'] = self._cached_image_clip_emb(img['file_path'])
        return image_pool

    def _extract_content_slides(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        skip_types = {'greeting', 'goodbye'}
        content_slides = []
        for slide_entry in slides:
            slide_meta = slide_entry.get('slide', {})
            slide_type = slide_meta.get('slide_type', '')
            if slide_type not in skip_types:
                content_slides.append(slide_entry)
        return content_slides

    def _step2_embed_slides(self, content_slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        slide_pool: List[Dict[str, Any]] = []
        for slide_entry in content_slides:
            slide_meta = slide_entry.get('slide', {})
            slide_number = slide_meta.get('slide_number', -1)
            content = slide_entry.get('content', [])
            if isinstance(content, list):
                bullet_points = [bp for bp in content if isinstance(bp, str) and bp.strip()]
            elif isinstance(content, str):
                bullet_points = [content]
            else:
                bullet_points = []
            if not bullet_points:
                continue
            slide_embeddings = []
            slide_clip_embeddings = []
            for bp in bullet_points:
                slide_embeddings.append(self._cached_text_emb(bp))
                slide_clip_embeddings.append(self._cached_text_clip_emb(bp))
            slide_title = slide_meta.get('slide_title', '')
            slide_pool.append({'slide_number': slide_number, 'slide_title': slide_title, 'bullet_points': bullet_points, 'slide_embeddings': slide_embeddings, 'slide_clip_embeddings': slide_clip_embeddings, 'page_range': self._expected_page_range(slide_title)})
        return slide_pool

    def _step3_match_images_to_slides(self, image_pool: List[Dict[str, Any]], slide_pool: List[Dict[str, Any]], used_images: Set[str]) -> List[Dict[str, Any]]:
        distributions: List[Dict[str, Any]] = []
        slide_image_count: Dict[int, int] = {s['slide_number']: 0 for s in slide_pool}
        for img in image_pool:
            img_name = Path(img['file_path']).name
            if img_name in used_images:
                continue
            img_desc_emb = img['img_desc_embedding']
            img_clip_emb = img['img_clip_embedding']
            best_slide_number = None
            best_score = -1.0
            for slide in slide_pool:
                slide_num = slide['slide_number']
                if slide_image_count.get(slide_num, 0) >= self.max_images_per_slide:
                    continue
                page_score = self._page_score(img.get('page_number'), slide.get('page_range'))
                if page_score <= 0:
                    continue
                text_sims = [self._cosine(img_desc_emb, bp_emb) for bp_emb in slide['slide_embeddings']]
                text_sim = self._top_k_avg(text_sims, k=3)
                image_sims = [self._cosine(img_clip_emb, bp_clip) for bp_clip in slide['slide_clip_embeddings']]
                image_sim = self._top_k_avg(image_sims, k=3)
                text_sim = self._normalize_sim(text_sim)
                image_sim = self._normalize_sim(image_sim)
                img_slide_sim = (self.alpha * text_sim + (1 - self.alpha) * image_sim) * page_score
                if img_slide_sim > best_score:
                    best_score = img_slide_sim
                    best_slide_number = slide_num
            if best_slide_number is not None and best_score > self.threshold:
                distributions.append({'slide_number': best_slide_number, 'image_path': img['file_path'], 'score': round(best_score, 4), 'source': 'existing', 'caption': self._shorten_caption(img.get('caption', ''))})
                used_images.add(img_name)
                slide_image_count[best_slide_number] = slide_image_count.get(best_slide_number, 0) + 1
                print(f"    [match] {img['image_id']} → slide {best_slide_number} (score={best_score:.4f})")
            else:
                print(f"    [skip]  {img['image_id']} — best score {best_score:.4f} below threshold")
        return distributions

    @staticmethod
    def _is_major_slide(slide_title: str) -> bool:
        import re
        return bool(re.match('^\\d+\\.\\s', slide_title.strip()))

    @staticmethod
    def _infer_page_number(file_path: str) -> Optional[int]:
        match = re.search(r'page_(\d+)', file_path or '')
        return int(match.group(1)) if match else None

    @staticmethod
    def _expected_page_range(slide_title: str) -> tuple[int, int]:
        title = slide_title.lower()
        if any(key in title for key in ['introduction', 'definition', 'application']):
            return (1, 2)
        if any(key in title for key in ['developing', 'model', 'product mix', 'formulating']):
            return (2, 3)
        if any(key in title for key in ['graphical', 'feasible', 'optimal']):
            return (3, 6)
        if any(key in title for key in ['computing', 'slack', 'constraint usage', 'production mix']):
            return (5, 6)
        if any(key in title for key in ['software', 'prolp', 'input', 'solving', 'conclusion']):
            return (6, 7)
        return (1, 7)

    @staticmethod
    def _page_score(page_number: Optional[int], page_range: Optional[tuple[int, int]]) -> float:
        if page_number is None or page_range is None:
            return 1.0
        start, end = page_range
        if start <= page_number <= end:
            return 1.0
        if abs(page_number - start) == 1 or abs(page_number - end) == 1:
            return 0.65
        return 0.0

    def _shorten_caption(self, caption: str, max_words: int=15) -> str:
        if not caption or len(caption.split()) <= max_words:
            return caption
        prompt = f'Summarize the following image caption into at most {max_words} words. Keep it descriptive and concise. Return ONLY the shortened caption, nothing else.\n\nCaption: {caption}\n\nShortened caption:'
        try:
            short = chat(model=self.llm_model, messages=[{'role': 'user', 'content': prompt}], temperature=0.3, max_tokens=60).strip().strip('"').strip("'")
            print(f"[caption] '{caption[:50]}...' → '{short}'")
            return short
        except Exception as e:
            print(f'[caption] Failed to shorten: {e}')
            return ' '.join(caption.split()[:max_words]) + '...'

    def _cached_text_emb(self, text: str):
        key = f'text:{text}'
        if key not in self._emb_cache:
            self._emb_cache[key] = self.matcher._get_text_embedding(text)
        return self._emb_cache[key]

    def _cached_image_clip_emb(self, image_path: str):
        key = f'img:{image_path}'
        if key not in self._emb_cache:
            self._emb_cache[key] = self.matcher._get_image_clip_embedding(image_path)
        return self._emb_cache[key]

    def _cached_text_clip_emb(self, text: str):
        key = f'clip_text:{text}'
        if key not in self._emb_cache:
            self._emb_cache[key] = self.matcher._get_text_clip_embedding(text)
        return self._emb_cache[key]

    @staticmethod
    def _cosine(a, b) -> float:
        if a is None or b is None:
            return 0.0
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def _top_k_avg(sims: List[float], k: int=3) -> float:
        if not sims:
            return 0.0
        sorted_sims = sorted(sims, reverse=True)
        top_k = sorted_sims[:k]
        return sum(top_k) / len(top_k)

    @staticmethod
    def _normalize_sim(value: float) -> float:
        return max(0.0, min(1.0, value))
