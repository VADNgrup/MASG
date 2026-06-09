from typing import List, Dict, Optional, Any, Set
import json
import re
from pathlib import Path
from src.utils.config import Config

class ImageDistribution:

    def __init__(self):
        self.threshold = Config.IMAGE_MATCH_THRESHOLD
        self.max_images_per_slide = Config.IMAGE_MATCH_MAX_IMAGES_PER_SLIDE
        self.stopwords = self._load_stopwords()

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
        print(f'\n  Step 0 complete: {len(image_pool)} context images prepared')
        source_pages_by_slide = self._load_slide_source_pages(lecture_id)
        slide_pool = self._step1_prepare_slides(content_slides, source_pages_by_slide, aggregated_media.get('page_count'))
        print(f'  Step 1 complete: {len(slide_pool)} content slides prepared')
        distributions = self._step2_match_images_to_slides(image_pool, slide_pool, used_images)
        print(f'  Step 2 complete: {len(distributions)} images matched to slides')
        
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
                image_description = self._clean_text(f'{caption} {reference_context}')
            else:
                image_description = self._clean_text(caption)
            if not image_description:
                image_description = "illustrative figure document diagram image"
            image_pool.append({'image_id': image_id, 'file_path': resolved_file_path, 'caption': caption, 'reference_context': reference_context, 'metadata': metadata, 'image_description': image_description, 'page_number': self._infer_page_number(file_path), 'tokens': self._tokens(image_description)})
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

    def _extract_content_slides(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        skip_types = {'greeting', 'goodbye'}
        content_slides = []
        for slide_entry in slides:
            slide_meta = slide_entry.get('slide', {})
            slide_type = slide_meta.get('slide_type', '')
            if slide_type not in skip_types:
                content_slides.append(slide_entry)
        return content_slides

    def _step1_prepare_slides(self, content_slides: List[Dict[str, Any]], source_pages_by_slide: Dict[int, List[int]], page_count: Optional[int]) -> List[Dict[str, Any]]:
        slide_pool: List[Dict[str, Any]] = []
        total_slides = len(content_slides)
        for idx, slide_entry in enumerate(content_slides):
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
            slide_title = slide_meta.get('slide_title', '')
            slide_text = self._clean_text(' '.join([slide_title] + bullet_points))
            page_range = self._source_page_range(source_pages_by_slide.get(slide_number)) or self._fallback_page_range(idx, total_slides, page_count)
            slide_pool.append({'slide_number': slide_number, 'slide_title': slide_title, 'bullet_points': bullet_points, 'tokens': self._tokens(slide_text), 'page_range': page_range})
        return slide_pool

    def _step2_match_images_to_slides(self, image_pool: List[Dict[str, Any]], slide_pool: List[Dict[str, Any]], used_images: Set[str]) -> List[Dict[str, Any]]:
        distributions: List[Dict[str, Any]] = []
        slide_image_count: Dict[int, int] = {s['slide_number']: 0 for s in slide_pool}
        for img in image_pool:
            img_name = Path(img['file_path']).name
            if img_name in used_images:
                continue
            best_slide_number = None
            best_score = -1.0
            for slide in slide_pool:
                slide_num = slide['slide_number']
                if slide_image_count.get(slide_num, 0) >= self.max_images_per_slide:
                    continue
                page_score = self._page_score(img.get('page_number'), slide.get('page_range'))
                if page_score <= 0:
                    continue
                text_sim = self._token_similarity(img.get('tokens', set()), slide.get('tokens', set()))
                
                # Dynamic page-match guarantee:
                # If the image resides on the exact same page as the slide (page_score == 1.0),
                # we provide a baseline text similarity boost (0.20) to guarantee it bypasses the threshold,
                # ensuring that relevant figures are preserved even if captions lack keyword overlap.
                effective_text_sim = text_sim
                if page_score == 1.0:
                    effective_text_sim = max(0.20, text_sim)
                elif page_score == 0.65:
                    effective_text_sim = max(0.12, text_sim)
                    
                spread_penalty = 0.55 ** slide_image_count.get(slide_num, 0)
                img_slide_sim = effective_text_sim * page_score * spread_penalty
                if img_slide_sim > best_score:
                    best_score = img_slide_sim
                    best_slide_number = slide_num
            if best_slide_number is not None and best_score > self.threshold:
                distributions.append({'slide_number': best_slide_number, 'image_path': img['file_path'], 'score': round(best_score, 4), 'source': 'existing', 'caption': self._best_caption(img)})
                used_images.add(img_name)
                slide_image_count[best_slide_number] = slide_image_count.get(best_slide_number, 0) + 1
                print(f"    [match] {img['image_id']} → slide {best_slide_number} (score={best_score:.4f})")
            else:
                print(f"    [skip]  {img['image_id']} — best score {best_score:.4f} below threshold")
        return distributions

    @staticmethod
    def _infer_page_number(file_path: str) -> Optional[int]:
        match = re.search(r'page_(\d+)', file_path or '')
        return int(match.group(1)) if match else None

    @staticmethod
    def _source_page_range(source_pages: Optional[List[int]]) -> Optional[tuple[int, int]]:
        pages = sorted({int(page) for page in (source_pages or []) if isinstance(page, int) or str(page).isdigit()})
        if not pages:
            return None
        return (pages[0], pages[-1])

    @staticmethod
    def _fallback_page_range(slide_index: int, total_slides: int, page_count: Optional[int]) -> Optional[tuple[int, int]]:
        try:
            page_count = int(page_count or 0)
        except (TypeError, ValueError):
            return None
        if not page_count or page_count <= 0 or total_slides <= 0:
            return None
        center = round(1 + slide_index * max(0, page_count - 1) / max(1, total_slides - 1))
        start = max(1, center - 1)
        end = min(page_count, center + 1)
        return (start, end)

    @staticmethod
    def _load_slide_source_pages(lecture_id: str) -> Dict[int, List[int]]:
        packet_path = Config.LECTURES_DIR / lecture_id / f'{lecture_id}_slide_packets.json'
        if not packet_path.exists():
            return {}
        try:
            packets = json.loads(packet_path.read_text(encoding='utf-8'))
        except Exception:
            return {}
        result: Dict[int, List[int]] = {}
        for packet in packets if isinstance(packets, list) else []:
            slide_number = packet.get('slide_number')
            pages = packet.get('source_pages') or []
            if slide_number is None:
                continue
            clean_pages = [int(page) for page in pages if isinstance(page, int) or str(page).isdigit()]
            if clean_pages:
                result[int(slide_number)] = clean_pages
        return result

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
        return ' '.join(caption.split()[:max_words]) + '...'

    def _best_caption(self, img: Dict[str, Any]) -> str:
        candidates = [
            img.get('caption', ''),
            img.get('reference_context', ''),
            img.get('image_description', ''),
        ]
        for candidate in candidates:
            clean = self._clean_caption(candidate)
            if clean:
                return self._shorten_caption(clean)
        return ''

    @staticmethod
    def _clean_caption(text: str) -> str:
        clean = re.sub(r'\s+', ' ', text or '').strip()
        clean = re.sub(r'!\[[^\]]*\]\([^)]+\)', ' ', clean, flags=re.IGNORECASE)
        clean = re.sub(r'#{1,6}\s*', ' ', clean)
        clean = re.sub(r'\*+\s*(?:figure|fig\.?|table|hình|bảng)\s*:\s*', ' ', clean, flags=re.IGNORECASE)
        clean = clean.replace('*', ' ')
        clean = re.sub(r'<!--\s*PAGE\s+\d+\s*-->', ' ', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b[a-zA-Z0-9_\-/]+\.(?:png|jpe?g|webp)\b', ' ', clean, flags=re.IGNORECASE)
        clean = re.sub(r'/assets/\S+|\bassets/\S+', ' ', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip(' -:;,.')
        if not clean:
            return ''
        if '/' in clean and len(clean.split()) <= 4:
            return ''
        if any(token in clean for token in ['![', '](', '##', '# ']):
            return ''
        if len(clean.split()) > 12:
            clean = ' '.join(clean.split()[:12])
        return clean

    def _tokens(self, text: str) -> Set[str]:
        words = re.findall(r'[A-Za-zÀ-ỹ0-9]{2,}', (text or '').lower())
        return {word for word in words if word not in self.stopwords}

    @staticmethod
    def _load_stopwords() -> Set[str]:
        path = Config.IMAGE_MATCH_STOPWORDS_PATH
        if not path.exists():
            return set()
        return {
            line.strip().lower()
            for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip()
        }

    @staticmethod
    def _token_similarity(left: Set[str], right: Set[str]) -> float:
        if not left or not right:
            return 0.0
        overlap = len(left & right)
        return overlap / max(4, min(len(left), len(right)))

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text or '').strip()
