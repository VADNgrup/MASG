from __future__ import annotations
import json
import os
import random
import re
import shutil
import logging
from collections import defaultdict
from pathlib import Path
from PIL import Image
from typing import Dict, List, Optional
from src.generator.slide_layout_manager import SlideLayoutManager
from src.generator.theme_selection import select_theme
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SLIDEV_DIR = _PROJECT_ROOT / 'src' / 'generator' / 'slidev'
_PUBLIC_ASSETS = _SLIDEV_DIR / 'public' / 'assets'
_OUTPUT_MD = _SLIDEV_DIR

def _to_assets_path(original_path: str) -> str:
    return '/assets/' + Path(original_path).name

class SlidePickMerge:

    def __init__(self, lecture_json_path: str, lecture_title: str, speaker_information: str):
        self.lecture_json_path = Path(lecture_json_path).resolve()
        self.lecture_title = lecture_title
        self.speaker_information = speaker_information
        stem = self.lecture_json_path.stem
        parent = self.lecture_json_path.parent
        self.image_dist_path = parent / f'{stem}_image_distribution.json'
        self.table_dist_path = parent / f'{stem}_table_distribution.json'
        self.outline_path = parent / f'{stem}_outline.md'
        with open(self.lecture_json_path, encoding='utf-8') as f:
            self._lecture = json.load(f)
        self.lecture_id = self._lecture['lecture_id']
        self.source_doc_id = self._lecture['metadata']['source_document_id']
        self.slides = self._lecture['slides']
        self._image_dist: Dict[int, List[dict]] = self._load_image_dist()
        self._table_dist: Dict[int, dict] = self._load_table_dist()
        outline_md = self.outline_path.read_text(encoding='utf-8') if self.outline_path.exists() else ''
        (self.theme, self.font) = select_theme(outline_md)
        logging.info(f'====> Selected theme: {self.theme}')
        self._mgr = SlideLayoutManager(theme=self.theme, font_sans=self.font, font_serif=self.font, font_mono=self.font, title=self.lecture_title, author=self.speaker_information)
        self._layout_log: List[dict] = []
        self._slide_counter: int = 0

    def _load_image_dist(self) -> Dict[int, List[dict]]:
        if not self.image_dist_path.exists():
            return {}
        with open(self.image_dist_path, encoding='utf-8') as f:
            items = json.load(f)
        result: Dict[int, List[dict]] = defaultdict(list)
        for item in items:
            result[int(item['slide_number'])].append(item)
        return dict(result)

    def _load_table_dist(self) -> Dict[int, dict]:
        if not self.table_dist_path.exists():
            return {}
        with open(self.table_dist_path, encoding='utf-8') as f:
            items = json.load(f)
        return {int(item['slide_number']): item for item in items}

    def _clear_public_assets(self):
        if _PUBLIC_ASSETS.exists():
            shutil.rmtree(_PUBLIC_ASSETS)
        _PUBLIC_ASSETS.mkdir(parents=True, exist_ok=True)

    def _copy_assets(self):
        base = _PROJECT_ROOT / 'data' / 'assets' / self.source_doc_id
        for sub in ('images', 'downloaded_images'):
            folder = base / sub
            if folder.exists():
                for f in folder.iterdir():
                    if f.is_file():
                        shutil.copy2(f, _PUBLIC_ASSETS / f.name)
        downloaded = _PROJECT_ROOT / 'data' / 'lectures' / self.lecture_id / 'downloaded_images'
        if downloaded.exists():
            for f in downloaded.iterdir():
                if f.is_file():
                    shutil.copy2(f, _PUBLIC_ASSETS / f.name)

    def _img_aspect_ratio(self, img_path: str) -> float:
        try:
            resolved = _PROJECT_ROOT / Path(img_path.replace('\\', '/'))
            with Image.open(resolved) as img:
                (w, h) = img.size
                return w / h if h else 0.0
        except Exception:
            return 1.0

    def _log_layout(self, slide_num, func_name: str, args: dict) -> None:
        self._layout_log.append({'slide_num': slide_num, 'layout_function_name': func_name, 'args': args})

    def _parse_outline(self) -> List[str]:
        counter = 0
        results: List[str] = []
        if not self.outline_path.exists():
            for slide_entry in self.slides:
                slide_info = slide_entry.get('slide', {}) if isinstance(slide_entry, dict) else {}
                text = str(slide_info.get('slide_title') or '').strip()
                text = re.sub(r'^\s*\d+(?:\.\d+)*[.)]?\s*', '', text).strip()
                if not text:
                    continue
                counter += 1
                results.append(f'{counter}. {text}')
            return results
        with open(self.outline_path, encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                m = re.match('^(#{1,6})\\s+(.*)', line)
                if not m:
                    continue
                depth = len(m.group(1))
                if depth != 1:
                    continue
                text = m.group(2).strip()
                counter += 1
                results.append(f'{counter}. {text}')
        return results

    def _toc_two_col_split(self, contents: List[str]) -> tuple[List[str], List[str]]:

        def _is_major(item: str) -> bool:
            return bool(re.match('^\\d+\\.\\s+\\S', item)) and item.split('.')[0].strip().isdigit()
        total = sum((len(s) for s in contents))
        target = total / 2
        running = 0
        mid_idx = len(contents) // 2
        for (i, item) in enumerate(contents):
            running += len(item)
            if running >= target:
                mid_idx = i
                break
        split_idx = None
        for i in range(mid_idx, len(contents)):
            if _is_major(contents[i]):
                split_idx = i
                break
        if split_idx is None or split_idx == 0:
            split_idx = max(1, mid_idx)
        return (contents[:split_idx], contents[split_idx:])

    def _build_toc_slide(self, contents: List[str]) -> str:
        mgr = self._mgr
        if len(contents) > 15:
            contents = [item for item in contents if re.match('^\\d+\\.\\s+\\S', item) and item.split('.')[0].strip().isdigit()]
        self._slide_counter += 1
        self._log_layout(self._slide_counter, 'toc_layout', {'toc_content': contents, 'heading': 'Outline'})
        return mgr.toc_layout(contents, heading='Outline')

    def _pick_image_layout(self, slide_num: int, title: str, contents: List[str], img_url: str, img_path: str, img2_url: Optional[str]=None, img2_path: Optional[str]=None, caption: Optional[str]=None, caption2: Optional[str]=None) -> str:
        mgr = self._mgr
        caption = self._normalise_image_caption(caption, title)
        caption2 = self._normalise_image_caption(caption2, title)
        if img2_url and img2_path:
            ratio1 = self._img_aspect_ratio(img_path)
            ratio2 = self._img_aspect_ratio(img2_path)
            both_landscape = ratio1 >= 1.77 and ratio2 >= 1.77
            if both_landscape:
                _args = {'title': title, 'content': contents, 'img1_path': img_url, 'img2_path': img2_url, 'image_width': '60%', 'caption1': caption, 'caption2': caption2}
                if random.random() < 0.5:
                    self._log_layout(slide_num, 'two_image_above_layout', _args)
                    return mgr.two_image_above_layout(title, contents, img_url, img2_url, image_width='60%', caption1=caption, caption2=caption2)
                else:
                    self._log_layout(slide_num, 'two_image_below_layout', _args)
                    return mgr.two_image_below_layout(title, contents, img_url, img2_url, image_width='60%', caption1=caption, caption2=caption2)
            else:
                _args = {'title': title, 'content': contents, 'img1_path': img_url, 'img2_path': img2_url, 'image_width': '30%', 'caption1': caption, 'caption2': caption2}
                if random.random() < 0.5:
                    self._log_layout(slide_num, 'two_image_right_layout', _args)
                    return mgr.two_image_right_layout(title, contents, img_url, img2_url, caption1=caption, caption2=caption2)
                else:
                    self._log_layout(slide_num, 'two_image_left_layout', _args)
                    return mgr.two_image_left_layout(title, contents, img_url, img2_url, caption1=caption, caption2=caption2)
        ratio = self._img_aspect_ratio(img_path)
        _args = {'title': title, 'content': contents, 'img_path': img_url, 'image_width': '40%', 'caption': caption}
        if ratio > 1.77:
            if random.random() < 0.5:
                self._log_layout(slide_num, 'image_above_layout', _args)
                return mgr.image_above_layout(title, contents, img_url, caption=caption)
            else:
                self._log_layout(slide_num, 'image_below_layout', _args)
                return mgr.image_below_layout(title, contents, img_url, caption=caption)
        elif random.random() < 0.5:
            self._log_layout(slide_num, 'image_right_layout', _args)
            return mgr.image_right_layout(title, contents, img_url, caption=caption)
        else:
            self._log_layout(slide_num, 'image_left_layout', _args)
            return mgr.image_left_layout(title, contents, img_url, caption=caption)

    @staticmethod
    def _normalise_image_caption(caption: Optional[str], slide_title: str) -> Optional[str]:
        text = re.sub(r'\s+', ' ', str(caption or '')).strip()
        text = re.sub(r'!\[[^\]]*\]\([^)]+\)', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'#{1,6}\s*', ' ', text)
        text = re.sub(r'\*+\s*(?:figure|fig\.?|table|hình|bảng)\s*:\s*', ' ', text, flags=re.IGNORECASE)
        text = text.replace('*', ' ')
        text = re.sub(r'\b[a-zA-Z0-9_\-/]+\.(?:png|jpe?g|webp)\b', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'/assets/\S+|\bassets/\S+', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'<!--\s*PAGE\s+\d+\s*-->', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip(' -:;,.')
        if not text:
            return None
        if '/' in text and len(text.split()) <= 4:
            return None
        if any(token in text for token in ['![', '](', '##', '# ']):
            return None
        if len(text.split()) > 12:
            text = ' '.join(text.split()[:12])
        if len(text.split()) <= 2 and text.lower() == slide_title.strip().lower():
            return None
        return text

    @staticmethod
    def _strip_table_bullets(contents: list) -> list:
        if not isinstance(contents, list):
            return contents
        cleaned = []
        for item in contents:
            if isinstance(item, dict) and 'table_markdown' in item:
                continue
            if isinstance(item, str):
                s = item.strip()
                if s.startswith('|') and s.endswith('|'):
                    continue
                if 'table_markdown' in s and ('|' in s):
                    continue
                if s.count('|') >= 6:
                    continue
                parts = SlidePickMerge._split_bullet_text(s)
                cleaned.extend(parts)
                continue
            cleaned.append(item)
        return cleaned

    @staticmethod
    def _split_bullet_text(text: str) -> List[str]:
        text = str(text).strip()
        if not text:
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) > 1:
            parts = []
            for line in lines:
                line = re.sub(r'^[-*•]\s+', '', line).strip()
                if line:
                    parts.append(line)
            return parts
        return [text]

    @staticmethod
    def _sanitise_latex(latex: str) -> str:
        if not latex:
            return ""
        s = latex.replace("\\n", " ")
        s = s.strip()
        if s.startswith("$$") and s.endswith("$$"):
            s = s[2:-2].strip()
        elif s.startswith("$") and s.endswith("$"):
            s = s[1:-1].strip()
        return s

    @staticmethod
    def _normalise_contents(raw_contents):
        def _compact(items):
            compacted = []
            for item in items:
                text = re.sub(r"\s+", " ", str(item).strip())
                if not text:
                    continue
                compacted.append(text)
            return SlidePickMerge._merge_fragments(compacted)[:9]

        if isinstance(raw_contents, list):
            cleaned = SlidePickMerge._strip_table_bullets(raw_contents)
            items = [str(item).strip() for item in cleaned if isinstance(item, str) and str(item).strip()]
            return _compact(items)
        if isinstance(raw_contents, str):
            text = re.sub(r'\s+', ' ', raw_contents).strip()
            if not text:
                return []
            sentences = re.split(r'(?<=[.!?])\s+', text)
            bullets = [s.strip() for s in sentences if s.strip()]
            return _compact(bullets[:10] if bullets else [text])
        if isinstance(raw_contents, dict):
            return raw_contents
        return []

    @staticmethod
    def _merge_fragments(items: List[str]) -> List[str]:
        merged: List[str] = []
        for item in items:
            text = re.sub(r"\s+", " ", str(item or "")).strip()
            if not text:
                continue
            starts_fragment = bool(re.match(r"^(?:and|or|but|with|while|plus|including|such as|each|plus|and each|32gb|16gb|250gb|40gb)\b", text, flags=re.IGNORECASE))
            
            is_cjk = any('\u4e00' <= char <= '\u9fff' for char in text)
            if is_cjk:
                too_short = len(text) <= 12 and bool(re.search(r"\d|gb|mb|cores?|ram|disk", text, flags=re.IGNORECASE))
            else:
                too_short = len(text.split()) <= 4 and bool(re.search(r"\d|gb|mb|cores?|ram|disk", text, flags=re.IGNORECASE))
                
            if merged and (starts_fragment or too_short):
                merged[-1] = re.sub(r"\s+", " ", f"{merged[-1].rstrip(' .;:,')}, {text.lstrip(' ,;:.')}")
                continue
            merged.append(text)
        return merged

    def _build_content_slide(self, slide_entry: dict) -> str:
        slide_info = slide_entry['slide']
        num = int(slide_info['slide_number'])
        title = slide_info['slide_title']
        stype = slide_info['slide_type']
        raw_contents = slide_entry.get('content', [])
        contents = self._normalise_contents(raw_contents)
        
        # Remove any content bullet point that is identical to the slide title (ignoring number prefixes)
        if isinstance(contents, list):
            cleaned_contents = []
            clean_title = re.sub(r'^\s*\d+(?:\.\d+)*\.\s*', '', title).strip().lower()
            for c in contents:
                clean_c = re.sub(r'^\s*\d+(?:\.\d+)*\.\s*', '', str(c)).strip().lower()
                if clean_c == clean_title:
                    continue
                cleaned_contents.append(c)
            contents = cleaned_contents
            
        mgr = self._mgr
        self._slide_counter += 1
        sn = self._slide_counter
        has_images = num in self._image_dist
        has_table_dist = num in self._table_dist
        if stype == 'comparison':
            if isinstance(contents, str) and '|' in contents:
                table_md = contents
                self._log_layout(sn, 'comparison_layout', {'title': title, 'table_markdown': table_md})
                return mgr.comparison_layout(title, table_md)
            self._log_layout(sn, 'only_content', {'title': title, 'content': contents})
            return mgr.only_content(title, contents if isinstance(contents, list) else [str(contents)])
        if stype == 'two_sub_contents':
            if isinstance(contents, list) and len(contents) <= 2:
                # Downgrade to standard single column bullet slide!
                self._log_layout(sn, 'only_content', {'title': title, 'content': contents})
                return mgr.only_content(title, contents)
            if isinstance(contents, dict):
                keys = list(contents.keys())
                sub_title_1 = keys[0] if len(keys) > 0 else 'Part 1'
                sub_title_2 = keys[1] if len(keys) > 1 else 'Part 2'
                sub_content_1 = contents.get(sub_title_1, [])
                sub_content_2 = contents.get(sub_title_2, [])
            else:
                mid = (len(contents) + 1) // 2
                (sub_title_1, sub_title_2) = ('Part 1', 'Part 2')
                sub_content_1 = contents[:mid]
                sub_content_2 = contents[mid:]
            self._log_layout(sn, 'two_contents_in_a_slide_layout', {'title': title, 'sub_title_1': sub_title_1, 'sub_title_2': sub_title_2, 'sub_content_1': sub_content_1, 'sub_content_2': sub_content_2})
            return mgr.two_contents_in_a_slide_layout(title, sub_title_1, sub_title_2, sub_content_1, sub_content_2)
        if stype == 'have_formula':
            latex = self._sanitise_latex(slide_info.get('latex_block_formula') or '')
            _args = {'title': title, 'latex_formula_block': latex, 'content': contents}
            if random.random() < 0.5:
                self._log_layout(sn, 'formula_top_layout', _args)
                return mgr.formula_top_layout(title, latex, contents)
            else:
                self._log_layout(sn, 'formula_below_layout', _args)
                return mgr.formula_below_layout(title, latex, contents)
        if stype == 'have_table':
            table_obj = slide_info.get('table') or {}
            table_caption = table_obj.get('table_caption', None)
            if has_table_dist:
                # Use the original table screenshot instead of a generated chart
                image_table_path = self._table_dist[num].get('image_table_path')
                if image_table_path and image_table_path != 'None':
                    image_url = _to_assets_path(image_table_path)
                    ratio = self._img_aspect_ratio(image_table_path)
                    image_width = '90%' if ratio >= 1.0 else '60%'
                    self._log_layout(sn, 'image_above_layout', {'title': title, 'content': [], 'img_path': image_url, 'image_width': image_width, 'caption': table_caption})
                    return mgr.image_above_layout(title, [], image_url, image_width=image_width, caption=table_caption)
            if has_images:
                img_entries = self._image_dist[num]
                if len(img_entries) >= 2:
                    img1 = img_entries[0]
                    img2 = img_entries[1]
                    return self._pick_image_layout(sn, title, contents, _to_assets_path(img1['image_path']), img1['image_path'], _to_assets_path(img2['image_path']), img2['image_path'], caption=img1.get('caption'), caption2=img2.get('caption'))
                else:
                    img = img_entries[0]
                    return self._pick_image_layout(sn, title, contents, _to_assets_path(img['image_path']), img['image_path'], caption=img.get('caption'))
            table_md = table_obj.get('table_markdown') or ''
            if table_md and '|' in table_md:
                self._log_layout(sn, 'comparison_layout', {'title': title, 'table_markdown': table_md})
                return mgr.comparison_layout(title, table_md)
            self._log_layout(sn, 'only_content', {'title': title, 'content': contents})
            return mgr.only_content(title, contents)
        if has_images:
            img_entries = self._image_dist[num]
            if len(img_entries) >= 2:
                img1 = img_entries[0]
                img2 = img_entries[1]
                return self._pick_image_layout(sn, title, contents, _to_assets_path(img1['image_path']), img1['image_path'], _to_assets_path(img2['image_path']), img2['image_path'], caption=img1.get('caption'), caption2=img2.get('caption'))
            else:
                img = img_entries[0]
                return self._pick_image_layout(sn, title, contents, _to_assets_path(img['image_path']), img['image_path'], caption=img.get('caption'))
        if has_table_dist:
            tbl_entry = self._table_dist[num]
            image_table_path = tbl_entry.get('image_table_path')
            if image_table_path and image_table_path != 'None':
                image_url = _to_assets_path(image_table_path)
                table_caption = tbl_entry.get('table_caption')
                ratio = self._img_aspect_ratio(image_table_path)
                image_width = '90%' if ratio >= 1.0 else '60%'
                self._log_layout(sn, 'image_above_layout', {'title': title, 'content': [], 'img_path': image_url, 'image_width': image_width, 'caption': table_caption})
                return mgr.image_above_layout(title, [], image_url, image_width=image_width, caption=table_caption)
        if isinstance(contents, list):
            total_chars = sum((len(s) for s in contents))
            if (total_chars > 420 and len(contents) >= 4) or any(len(s) > 88 for s in contents):
                self._log_layout(sn, 'two_cols_content_layout', {'title': title, 'content': contents})
                return mgr.two_cols_content_layout(title, contents)
        self._log_layout(sn, 'only_content', {'title': title, 'content': contents})
        return mgr.only_content(title, contents)

    def build(self) -> str:
        self._clear_public_assets()
        self._copy_assets()
        self._slide_counter = 1
        short_title = self._summarise_title(self.lecture_title)
        doc = self._mgr.config_and_greeting_slide(short_title=short_title)
        self._log_layout(self._slide_counter, 'config_and_greeting_slide', {'short_title': short_title})
        toc_items = self._parse_outline()
        doc += self._build_toc_slide(toc_items)
        for slide_entry in self.slides:
            doc += self._build_content_slide(slide_entry)
        self._slide_counter += 1
        doc += self._mgr.end_layout(end_text='Thank you')
        self._log_layout(self._slide_counter, 'end_layout', {'end_text': 'Thank you'})
        self._validate_slide_markdown(doc)
        _OUTPUT_MD.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_MD / f'{self.lecture_id}.md'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        log_path = self.lecture_json_path.parent / f'{self.lecture_id}_layout_distribution.json'
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self._layout_log, f, ensure_ascii=False, indent=2)
        return doc

    @staticmethod
    def _validate_slide_markdown(doc: str) -> None:
        failures = []
        for idx, part in enumerate(doc.split('---'), start=1):
            if idx <= 3:
                continue
            if '<!-- END_SLIDE -->' in part:
                continue
            title_match = re.search(
                r'<(?:h1|div)[^>]*(?:data-slide-title="true"|class="generated-slide-title")[^>]*>(.*?)</(?:h1|div)>|^#\s+(.+)$',
                part,
                flags=re.MULTILINE | re.DOTALL,
            )
            if not title_match:
                continue
            title = re.sub('<[^>]+>', '', title_match.group(1) or title_match.group(2) or '').strip()
            if not title:
                continue
            if 'layout: cover' in part:
                continue
            has_body = any(token in part for token in ['<li', '<ul', '<img', '\n- ', '\n|'])
            if not has_body:
                failures.append(f'{idx}: {title}')
        if failures:
            raise RuntimeError('Empty slide body detected: ' + '; '.join(failures))

    def _summarise_title(self, title: str) -> str:
        text = re.sub(r'[_:;|]+', ' ', str(title or '')).strip()
        text = re.sub(r'\s+', ' ', text)
        words = text.split()
        if len(words) <= 6:
            return text
        return ' '.join(words[:6])
