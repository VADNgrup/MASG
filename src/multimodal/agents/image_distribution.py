from typing import List, Dict, Optional, Any, Set
import json
import requests
import base64
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from src.utils.config import config
from src.utils.llm import chat
from src.utils.semantic_match import SemanticMatcher
from src.ingestion.image_filter import ImageFilter
from src.utils.config import Config
from src.ingestion.vision_model import VisionCaptionGenerator

class ImageDistribution:

    def __init__(self):
        self.matcher = SemanticMatcher()
        self.llm_model = config.LLM_MODEL_NAME
        self.vlm_model = config.VLM_MODEL_NAME
        self.tavily_api_key = config.TAVILY_API_KEY
        self.num_images = 3
        self.skip_websites = ['researchgate.net', 'huggingface.co', 'towardsdatascience.com', 'mdpi.com']
        self.alpha = 0.7
        self.threshold = 0.28
        self.web_threshold = 0.35
        self.web_dedup_threshold = 0.85
        self.max_images_per_slide = 2
        self.fusion_threshold = 1.2
        self.width_threshold = 1.77
        self._emb_cache: Dict[str, Any] = {}
        self._image_filter = ImageFilter()
        self._selected_web_embs: List[Any] = []

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
        if slides_without_images and self.tavily_api_key:
            print(f'\n  Step 5: {len(slides_without_images)} slides still need images — searching web via Tavily...')
            download_dir = Path(f'data/assets/{lecture_id}/downloaded_images')
            download_dir.mkdir(parents=True, exist_ok=True)
            web_distributions = self._step5_web_search_fallback(slides_without_images, download_dir, used_images, aggregated_media)
            distributions.extend(web_distributions)
            print(f'  Step 5 complete: {len(web_distributions)} web images added')
        elif slides_without_images:
            print(f'\n  Step 5: {len(slides_without_images)} slides still need images — no TAVILY_API_KEY configured, skipping web fallback.')
        output_path = Path(f'data/lectures/{lecture_id}_image_distributions.json')
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
            if not file_path or not Path(file_path).exists():
                print(f'    [skip] Image file not found: {file_path}')
                continue
            if reference_context:
                image_description = self._generate_image_description(caption, reference_context)
            else:
                image_description = caption
            image_pool.append({'image_id': image_id, 'file_path': file_path, 'caption': caption, 'reference_context': reference_context, 'metadata': metadata, 'image_description': image_description})
            print(f'    [desc] {image_id}: {image_description[:80]}...')
        return image_pool

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
            slide_pool.append({'slide_number': slide_number, 'slide_title': slide_meta.get('slide_title', ''), 'bullet_points': bullet_points, 'slide_embeddings': slide_embeddings, 'slide_clip_embeddings': slide_clip_embeddings})
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
                text_sims = [self._cosine(img_desc_emb, bp_emb) for bp_emb in slide['slide_embeddings']]
                text_sim = self._top_k_avg(text_sims, k=3)
                image_sims = [self._cosine(img_clip_emb, bp_clip) for bp_clip in slide['slide_clip_embeddings']]
                image_sim = self._top_k_avg(image_sims, k=3)
                text_sim = self._normalize_sim(text_sim)
                image_sim = self._normalize_sim(image_sim)
                img_slide_sim = self.alpha * text_sim + (1 - self.alpha) * image_sim
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

    def _step5_web_search_fallback(self, slides_without_images: List[Dict[str, Any]], download_dir: Path, used_images: Set[str], aggregated_media: Dict[str, Any]) -> List[Dict[str, Any]]:
        distributions: List[Dict[str, Any]] = []
        for slide_info in slides_without_images:
            slide_number = slide_info['slide_number']
            slide_title = slide_info.get('slide_title', '')
            bullet_points = slide_info.get('bullet_points', [])
            if self._is_major_slide(slide_title):
                print(f"    [web] Slide {slide_number}: skipped (major slide '{slide_title}')")
                continue
            slide_text = f'{slide_title}. ' + ' '.join(bullet_points)
            queries = self._generate_search_queries(slide_text)
            if not queries:
                print(f'    [web] Slide {slide_number}: failed to generate queries')
                continue
            slide_selected_count = 0
            first_image_info = None
            for (q_idx, query) in enumerate(queries, start=1):
                if slide_selected_count >= self.max_images_per_slide:
                    break
                if q_idx == 2 and first_image_info is not None:
                    (w1, h1) = first_image_info
                    if w1 > 0 and h1 > 0:
                        if h1 / w1 > self.fusion_threshold:
                            print(f'[web] Slide {slide_number}: 1st image too tall (h/w={h1 / w1:.2f} > {self.fusion_threshold}) → skip 2nd query')
                            break
                        if w1 / h1 > self.width_threshold:
                            print(f'[web] Slide {slide_number}: 1st image too wide (w/h={w1 / h1:.2f} > {self.width_threshold}) → skip 2nd query')
                            break
                print(f"[web] Slide {slide_number} query {q_idx}/{len(queries)}: '{query[:60]}...'")
                downloaded_paths = self._search_and_download_images(query=query, download_dir=download_dir, slide_number=slide_number, query_idx=q_idx)
                if not downloaded_paths:
                    print(f'[web] Slide {slide_number} query {q_idx}: no images downloaded')
                    continue
                query_clip_emb = self._cached_text_clip_emb(query)
                scored: List[Dict[str, Any]] = []
                for img_path in downloaded_paths:
                    img_name = Path(img_path).name
                    if img_name in used_images:
                        continue
                    try:
                        img_clip_emb = self._cached_image_clip_emb(str(img_path))
                        sim = self._cosine(query_clip_emb, img_clip_emb)
                        sim = self._normalize_sim(sim)
                        scored.append({'path': str(img_path), 'score': sim, 'name': img_name, 'clip_emb': img_clip_emb})
                    except Exception as e:
                        print(f'[web] Error embedding {img_name}: {e}')
                if not scored:
                    continue
                scored.sort(key=lambda x: x['score'], reverse=True)
                selected_candidate = None
                for candidate in scored:
                    if candidate['score'] < self.web_threshold:
                        print(f"[web] Slide {slide_number} query {q_idx}: best {candidate['name']} score {candidate['score']:.4f} below threshold → skip")
                        break
                    is_duplicate = False
                    for prev_emb in self._selected_web_embs:
                        dup_sim = self._cosine(candidate['clip_emb'], prev_emb)
                        dup_sim = self._normalize_sim(dup_sim)
                        if dup_sim > self.web_dedup_threshold:
                            print(f"[web] Slide {slide_number} query {q_idx}: {candidate['name']} too similar to a previous image (sim={dup_sim:.4f}) → skip")
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        selected_candidate = candidate
                        break
                if not selected_candidate:
                    print(f'[web] Slide {slide_number} query {q_idx}: no suitable image found')
                    continue
                    
                print(f"[web] Slide {slide_number} query {q_idx}: Validating {selected_candidate['name']} with VLM...")
                vlm = VisionCaptionGenerator()
                with open(selected_candidate['path'], "rb") as img_file:
                    img_bytes = img_file.read()
                vlm_caption = vlm.generate_caption(img_bytes, slide_text)
                if "error" in vlm_caption.lower() or len(vlm_caption) < 5:
                     print(f"[web] Slide {slide_number} query {q_idx}: VLM rejected {selected_candidate['name']}")
                     continue

                relevance_prompt = f'Is this image directly relevant to the following slide topic? Answer ONLY "yes" or "no".\n\nSlide topic: {slide_text[:500]}\nImage description: {vlm_caption}'
                try:
                    relevance_answer = chat(model=self.llm_model, messages=[{'role': 'user', 'content': relevance_prompt}], temperature=0, max_tokens=10).strip().lower()
                    if 'no' in relevance_answer:
                        print(f"[web] Slide {slide_number} query {q_idx}: LLM says image is NOT relevant to slide topic → skip")
                        continue
                except Exception:
                    pass

                try:
                    with Image.open(selected_candidate['path']) as pil_img:
                        (cand_w, cand_h) = pil_img.size
                except Exception:
                    (cand_w, cand_h) = (0, 0)
                if q_idx == 2 and first_image_info is not None and (cand_w > 0) and (cand_h > 0):
                    (w1, h1) = first_image_info
                    scale = w1 / cand_w
                    h2_norm = cand_h * scale
                    fusion_ratio = (h1 + h2_norm) / w1
                    if fusion_ratio >= self.fusion_threshold:
                        print(f'[web] Slide {slide_number}: combined ratio {fusion_ratio:.2f} >= {self.fusion_threshold} → reject 2nd image')
                        continue
                    print(f'[web] Slide {slide_number}: combined ratio {fusion_ratio:.2f} < {self.fusion_threshold} → accept 2nd image')
                distributions.append({'slide_number': slide_number, 'image_path': selected_candidate['path'], 'score': round(selected_candidate['score'], 4), 'source': 'downloaded', 'caption': self._shorten_caption(vlm_caption)})
                used_images.add(selected_candidate['name'])
                self._selected_web_embs.append(selected_candidate['clip_emb'])
                self._add_downloaded_to_media(selected_candidate['path'], slide_number, query, aggregated_media)
                slide_selected_count += 1
                print(f"[web] Slide {slide_number} query {q_idx}: selected {selected_candidate['name']} (score={selected_candidate['score']:.4f})")
                if q_idx == 1 and cand_w > 0 and (cand_h > 0):
                    first_image_info = (cand_w, cand_h)
        return distributions

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

    def _generate_search_queries(self, slide_text: str) -> List[str]:
        prompt = f'You are an expert at generating image search queries for educational presentations. Given the following slide content, generate exactly 2 concise search queries (10-20 words each) that would find relevant and illustrative images for this slide. The two queries should target DIFFERENT visual aspects of the slide content to maximize the diversity of images found.\n\nReturn ONLY the two queries, one per line, numbered as:\n1. <query1>\n2. <query2>\n\nSlide content: {slide_text[:1000]}\n\nSearch queries:'
        try:
            raw = chat(model=self.llm_model, messages=[{'role': 'user', 'content': prompt}], temperature=0.3, max_tokens=200).strip()
            queries = []
            for line in raw.split('\n'):
                line = line.strip()
                if line and line[0].isdigit() and ('.' in line[:3]):
                    line = line.split('.', 1)[1].strip()
                line = line.strip('"').strip("'")
                if line:
                    queries.append(line)
            return queries[:2]
        except Exception as e:
            print(f'[LLM] Failed to generate search queries: {e}')
            return []

    def _add_downloaded_to_media(self, img_path_str: str, slide_number: int, caption: str, aggregated_media: Dict[str, Any]):
        img_path = Path(img_path_str)
        try:
            with Image.open(img_path) as pil_img:
                (width, height) = pil_img.size
                fmt = pil_img.format or 'PNG'
            file_size_kb = round(img_path.stat().st_size / 1024, 2)
        except Exception:
            (width, height, fmt, file_size_kb) = (0, 0, 'PNG', 0.0)
        new_entry = {'image_id': f'downloaded_slide{slide_number}', 'file_path': img_path_str, 'caption': caption, 'metadata': {'width': width, 'height': height, 'format': fmt.lower(), 'file_size_kb': file_size_kb}}
        aggregated_media.setdefault('images', []).append(new_entry)
        aggregated_media['total_images'] = len(aggregated_media['images'])
    MIN_WH_RATIO = Config.MIN_WH_RATIO_IMAGE_DOWNLOAD

    def _search_and_download_images(self, query: str, download_dir: Path, slide_number: int, query_idx: int=1) -> List[Path]:
        image_urls = self._search_images(query, max_results=6)
        if not image_urls:
            return []
        downloaded_paths: List[Path] = []
        for (idx, url) in enumerate(image_urls):
            if len(downloaded_paths) >= self.num_images:
                break
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                (passed, reason) = self._image_filter.pre_filter(response.content)
                if not passed:
                    print(f'[filter] Rejected — {reason}')
                    continue
                img = Image.open(BytesIO(response.content))
                (w, h) = img.size
                if h > 0 and w / h < self.MIN_WH_RATIO:
                    print(f'[filter] Rejected — w/h={w / h:.3f} < {self.MIN_WH_RATIO:.3f} (portrait image, url={url[:60]})')
                    continue
                file_name = f'slide_{slide_number}_q{query_idx}_serper_{idx + 1}.png'
                file_path = download_dir / file_name
                img.save(file_path, 'PNG')
                downloaded_paths.append(file_path)
            except Exception as e:
                print(f'[download] Failed: {str(e)[:80]}')
        return downloaded_paths

    def _search_images(self, query: str, max_results: int | None=None) -> List[str]:
        if max_results is None:
            max_results = self.num_images
            
        url = 'https://api.tavily.com/search'
        payload = json.dumps({
            'api_key': self.tavily_api_key,
            'query': query,
            'include_images': True,
            'search_depth': 'advanced'
        })
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            # Tavily returns an 'images' list containing image URLs
            results = response.json().get('images', [])
            image_urls = []
            for img_url in results:
                if len(image_urls) >= max_results:
                    break
                if not img_url:
                    continue
                if img_url.lower().endswith('.svg'):
                    continue
                if any((domain in img_url.lower() for domain in self.skip_websites)):
                    continue
                image_urls.append(img_url)
            return image_urls
        except Exception as e:
            print(f'[tavily] Error searching images: {e}')
            return []

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