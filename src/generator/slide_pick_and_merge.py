from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from PIL import Image
from typing import Dict, List, Optional

from src.generator.slide_layout_manager import SlideLayoutManager

# ---------------------------------------------------------------------------
# Paths (relative to project root, i.e. d:/python/LecSlideGen)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]   # …/LecSlideGen
_SLIDEV_DIR   = _PROJECT_ROOT / "src" / "generator" / "slidev"
_PUBLIC_ASSETS = _SLIDEV_DIR / "public" / "assets"
_OUTPUT_MD    = _SLIDEV_DIR


def _to_assets_path(original_path: str) -> str:
    """Convert any local path like data/... or data\\... to /assets/<basename>."""
    return "/assets/" + Path(original_path).name


class SlidePickMerge:
    # ------------------------------------------------------------------ init
    def __init__(
        self,
        lecture_json_path: str,
        lecture_title: str,
        speaker_information: str,
    ):
        self.lecture_json_path  = Path(lecture_json_path).resolve()
        self.lecture_title      = lecture_title
        self.speaker_information = speaker_information

        # Derive companion file paths
        stem = self.lecture_json_path.stem   # e.g. "lec_6895e38a"
        parent = self.lecture_json_path.parent
        self.image_dist_path  = parent / f"{stem}_image_distributions.json"
        self.table_dist_path  = parent / f"{stem}_table_distribution.json"
        self.outline_path     = parent / f"{stem}_outline.md"

        # Read lecture JSON
        with open(self.lecture_json_path, encoding="utf-8") as f:
            self._lecture = json.load(f)

        self.lecture_id        = self._lecture["lecture_id"]
        self.source_doc_id     = self._lecture["metadata"]["source_document_id"]
        self.slides            = self._lecture["slides"]

        # Build lookup dicts keyed by slide_number (int)
        self._image_dist: Dict[int, dict] = self._load_image_dist()
        self._table_dist: Dict[int, dict] = self._load_table_dist()

        self._mgr = SlideLayoutManager()

    # ------------------------------------------------------------------ loaders
    def _load_image_dist(self) -> Dict[int, dict]:
        if not self.image_dist_path.exists():
            return {}
        with open(self.image_dist_path, encoding="utf-8") as f:
            items = json.load(f)
        return {int(item["slide_number"]): item for item in items}

    def _load_table_dist(self) -> Dict[int, dict]:
        if not self.table_dist_path.exists():
            return {}
        with open(self.table_dist_path, encoding="utf-8") as f:
            items = json.load(f)
        return {int(item["slide_number"]): item for item in items}

    # ------------------------------------------------------------------ assets
    def _clear_public_assets(self):
        """Remove all files inside slidev/public/assets (keep the dir itself)."""
        if _PUBLIC_ASSETS.exists():
            shutil.rmtree(_PUBLIC_ASSETS)
        _PUBLIC_ASSETS.mkdir(parents=True, exist_ok=True)

    def _copy_assets(self):
        """Copy all relevant images/charts into public/assets."""
        # 1. data/assets/{source_document_id}/charts  and  .../images
        base = _PROJECT_ROOT / "data" / "assets" / self.source_doc_id
        for sub in ("charts", "images"):
            folder = base / sub
            if folder.exists():
                for f in folder.iterdir():
                    if f.is_file():
                        shutil.copy2(f, _PUBLIC_ASSETS / f.name)

        # 2. data/lectures/{lecture_id}/downloaded_images
        downloaded = _PROJECT_ROOT / "data" / "lectures" / self.lecture_id / "downloaded_images"
        if downloaded.exists():
            for f in downloaded.iterdir():
                if f.is_file():
                    shutil.copy2(f, _PUBLIC_ASSETS / f.name)

    def _img_aspect_ratio(self, img_path: str) -> float:
        """Return width/height ratio (>1.77 ⟹ landscape/wide)."""
        try:
            resolved = _PROJECT_ROOT / Path(img_path.replace("\\", "/"))
            with Image.open(resolved) as img:
                w, h = img.size
                return w / h if h else 0.0
        except Exception:
            return 1.0   # default: treat as portrait

    # ------------------------------------------------------------------ TOC
    def _parse_outline(self) -> List[str]:
        """
        Parse outline.md into numbered section strings, e.g.:
            # Intro          → "1. Intro"
            ## Background    → "1.1. Background"
            ## Motivation    → "1.2. Motivation"
            ### Details      → "1.2.1. Details"
            # Methods        → "2. Methods"
        """
        counters: List[int] = []   # stack of counters per depth level
        results: List[str] = []

        with open(self.outline_path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue

                # Count leading '#' characters
                m = re.match(r"^(#{1,6})\s+(.*)", line)
                if not m:
                    continue

                depth = len(m.group(1))   # 1 for #, 2 for ##, etc.
                text  = m.group(2).strip()

                # Extend or trim the counters stack to match current depth
                if depth > len(counters):
                    # Go deeper: add new counter levels initialised to 0
                    while len(counters) < depth:
                        counters.append(0)
                else:
                    # Go same level or up: reset all deeper levels
                    counters = counters[:depth]

                # Increment the counter at the current depth
                counters[depth - 1] += 1

                # Build prefix like "1.", "1.1.", "1.2.3."
                prefix = ".".join(str(c) for c in counters) + "."
                results.append(f"{prefix} {text}")

        return results


    def _toc_two_col_split(self, contents: List[str]) -> tuple[List[str], List[str]]:
        """
        Split TOC items into two columns.
        1. Find the index closest to the character midpoint.
        2. From that index, scan DOWNWARD until we hit a major section
           boundary (item matches "N. text" with no sub-numbering, e.g. "2. Dataset").
        3. Cut at that boundary so each column starts with a major section.
        Falls back to the midpoint index if no major section is found below.
        """
        def _is_major(item: str) -> bool:
            # Major section: starts with a single integer followed by ". "
            # e.g. "1. Introduction" → True
            # "1.1. Background"     → False
            return bool(re.match(r"^\d+\.\s+\S", item)) and \
                   item.split(".")[0].strip().isdigit()

        total = sum(len(s) for s in contents)
        target = total / 2

        # Step 1: find the index where cumulative chars first reach the midpoint
        running = 0
        mid_idx = len(contents) // 2
        for i, item in enumerate(contents):
            running += len(item)
            if running >= target:
                mid_idx = i
                break

        # Step 2: scan downward from mid_idx to find the next major section
        split_idx = None
        for i in range(mid_idx, len(contents)):
            if _is_major(contents[i]):
                split_idx = i
                break

        # Fallback: use mid_idx itself (or 1 to avoid empty left column)
        if split_idx is None or split_idx == 0:
            split_idx = max(1, mid_idx)

        return contents[:split_idx], contents[split_idx:]

    def _build_toc_slide(self, contents: List[str]) -> str:
        mgr = self._mgr

        # If the outline is large (> 15 items), condense to major sections only
        # before deciding on layout and splitting.
        if len(contents) > 15:
            contents = [
                item for item in contents
                if re.match(r"^\d+\.\s+\S", item) and item.split(".")[0].strip().isdigit()
            ]

        total_chars = sum(len(s) for s in contents)

        if total_chars < 600:
            return mgr._toc_single(self.lecture_title, contents)

        left, right = self._toc_two_col_split(contents)

        def _is_major(s: str) -> bool:
            return bool(re.match(r"^\d+\.\s+\S", s)) and s.split(".")[0].strip().isdigit()

        def _fmt(items: List[str]) -> str:
            lines = []
            for i, item in enumerate(items):
                is_last    = (i == len(items) - 1)
                next_major = (not is_last) and _is_major(items[i + 1])
                suffix = " " if is_last or next_major else " \\"
                lines.append(f" {item}{suffix}")
            return "\n".join(lines)

        return (
            f"\n"
            f"---\n"
            f"layout: two-cols-content\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{mgr._h1(self.lecture_title)}\n"
            f"\n"
            f"::left::\n"
            f"\n"
            f"{_fmt(left)}\n"
            f"\n"
            f"::right::\n"
            f"\n"
            f"{_fmt(right)}\n"
            f"---\n"
        )

    # ------------------------------------------------------------------ slides
    def _build_content_slide(self, slide: dict) -> str:
        num        = int(slide["slide_number"])
        title      = slide["slide_title"]
        contents   = slide.get("content", [])
        mgr        = self._mgr

        has_image = num in self._image_dist
        has_table = num in self._table_dist

        # ── case: image + table (two side images)
        if has_image and has_table:
            img_entry   = self._image_dist[num]
            tbl_entry   = self._table_dist[num]
            chart_path  = tbl_entry.get("chart_path")

            img1 = _to_assets_path(img_entry["image_path"])
            if chart_path and chart_path != "None":
                img2 = _to_assets_path(chart_path)
            else:
                # No chart image available – skip second image and treat as
                # single-image slide (fall through to image-only branch)
                has_table = False

            if has_table:
                return mgr.slide_with_two_side_image(title, contents, img1, img2)

        # ── case: image only
        if has_image:
            img_entry = self._image_dist[num]
            img_path  = img_entry["image_path"]
            img_url   = _to_assets_path(img_path)
            ratio     = self._img_aspect_ratio(img_path)

            if ratio > 1.77:
                return mgr.slide_with_one_above_image(title, contents, img_url)
            else:
                return mgr.slide_with_one_side_image(title, contents, img_url)

        # ── case: content only
        # If many bullet points → two-col, else single col
        total_chars = sum(len(s) for s in contents)
        if total_chars > 600 and len(contents) >= 4:
            return mgr.slide_two_contents(title, contents)
        return mgr.slide_only_content(title, contents)

    # ------------------------------------------------------------------ build
    def build(self) -> str:
        """
        Assemble the full .md document and write it to output_md/{lecture_id}.md.
        Returns the markdown string.
        """
        # 1. Prepare assets
        self._clear_public_assets()
        self._copy_assets()

        # 2. Config / global frontmatter
        doc = self._mgr.slide_config(
            title=self.lecture_title,
        )

        # 3. Greeting slide (plain h1/h2, shares frontmatter background)
        doc += self._mgr.greeting_slide(
            title=self.lecture_title,
            speaker_information=self.speaker_information,
        )

        # 4. Table of Contents
        toc_items = self._parse_outline()
        doc += self._build_toc_slide(toc_items)

        # 5. Content slides
        for slide in self.slides:
            if slide.get("slide_type") == "content":
                doc += self._build_content_slide(slide)

        # 6. Goodbye slide
        doc = doc + "---\n" + self._mgr.greet_and_goodbye_slide(
            title="Thanks for listening!",
            speaker_information=self.speaker_information,
        )

        # 7. Write output
        _OUTPUT_MD.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_MD / f"{self.lecture_id}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc)

        return doc


pickme = SlidePickMerge(
    lecture_json_path=r"D:\python\LecSlideGen\data\lectures\lec_6895e38a.json",
    lecture_title="Image Classification SOTA",
    speaker_information="Prof. Nguyen Khac An",
)
pickme.build()