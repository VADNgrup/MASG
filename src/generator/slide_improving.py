import os
import sys
import json
import logging
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from src.utils.config import Config
from src.utils.fuzzy_distance import fuzzy_distance

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))



class SlideImproving:
    """
    Per-slide image_width optimizer.

    For every slide that has an image the optimizer searches for the
    value of ``w`` (image_width in %) that simultaneously satisfies:

        f(w) = 1 - fuzzy_score(w) / 100  →  minimise (text must fit)
        g(w) = bg_pixels(w) / total_pixels →  minimise (reduce empty space)

    with the hard constraint  f(w) == 0  (all expected text is readable).

    No VLM is used anywhere in this class:
    - text is extracted with PyMuPDF
    - background colour is detected once via KMeans on the last slide
    """

    SLIDE_IMPROVING_MAX_ITERATION = Config.SLIDE_IMPROVING_MAX_ITERATION   # max gradient steps per slide

    def __init__(
        self,
        md_path: str,
        lecture_json_path: str,
        lecture_title: str = "",
        speaker_information: str = "",
        theme: str = "frankfurt",
        font: str = "STIX Two Text",
    ):
        # Resolve md_path
        _given = Path(md_path)
        _generator_dir = Path(__file__).parent
        if _given.is_absolute() and _given.exists():
            self.md_path = _given
        elif _given.resolve().exists():
            self.md_path = _given.resolve()
        elif (_generator_dir / _given).exists():
            self.md_path = (_generator_dir / _given).resolve()
        else:
            raise FileNotFoundError(
                f"Slide file not found: '{md_path}'.\n"
                f"Tried:\n  {_given.resolve()}\n  {(_generator_dir / _given).resolve()}"
            )

        self.slidev_dir = self.md_path.parent
        self.lecture_id = self.md_path.stem
        self.theme = theme
        self.font = font

        _lec_json = Path(lecture_json_path).resolve()
        self.layout_dist_path = _lec_json.parent / f"{self.lecture_id}_layout_distribution.json"

        self.lecture_title = lecture_title
        self.speaker_information = speaker_information

        # Step size for w adjustments (from config)
        self._step = float(Config.SLIDE_IMAGE_WIDTH_STEP)

        # Cached global values (computed once across all slides)
        self._bg_color: np.ndarray | None = None      # dominant background RGB

    def run(self) -> None:
        logger.info(f"[SlideImproving] Starting for lecture '{self.lecture_id}'")

        entries = self._read_layout_dist()

        # Find all slides that carry an image_width parameter
        image_slides = [e for e in entries if "image_width" in e.get("args", {})]

        if not image_slides:
            logger.info("[SlideImproving] No image slides found — nothing to optimise.")
        else:
            # ── Initialise shared constants from the LAST image slide ──────
            last_entry = image_slides[-1]
            self._init_global_constants(last_entry)

            # ── Optimise each image slide independently ────────────────────
            for entry in image_slides:
                slide_num = entry["slide_num"]
                logger.info(f"[SlideImproving] Optimising slide {slide_num} …")
                new_entry = self._optimise_slide(entry, entries)
                # Replace entry in-place
                idx = next(i for i, e in enumerate(entries) if e["slide_num"] == slide_num)
                entries[idx] = new_entry

            # Write updated layout distribution
            self._write_layout_dist(entries)

            # Regenerate the full .md from updated entries
            self._replay_layouts(entries)

        # Final full export
        self._export_pdf_full()
        logger.info("[SlideImproving] Finished.")

    def _init_global_constants(self, reference_entry: dict) -> None:
        """
        Export the reference (last image) slide, then:
          1. Measure slide dimensions → self._slide_total_pixels
          2. Detect dominant background colour via KMeans → self._bg_color
        """
        slide_num = reference_entry["slide_num"]
        logger.info(
            f"[SlideImproving] Initialising global constants from slide {slide_num} …"
        )
        self._export_pdf_single(slide_num)
        pdf_path = self.slidev_dir / f"{self.lecture_id}-export.pdf"

        doc = fitz.open(str(pdf_path))
        page = doc[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()

        arr = np.array(img)
        H, W = arr.shape[:2]

        # KMeans on a random sample of pixels (fast, one-off)
        pixels = arr.reshape(-1, 3).astype(float)
        sample_idx = np.random.choice(len(pixels), min(5000, len(pixels)), replace=False)
        sample = pixels[sample_idx]
        km = KMeans(n_clusters=3, n_init=3, random_state=42)
        km.fit(sample)
        labels, counts = np.unique(km.labels_, return_counts=True)
        bg_label = labels[np.argmax(counts)]
        self._bg_color = km.cluster_centers_[bg_label]

        logger.info(
            f"[SlideImproving] slide size={W}×{H} px  "
            f"bg_color=({self._bg_color[0]:.0f},{self._bg_color[1]:.0f},{self._bg_color[2]:.0f})"
        )

    def _optimise_slide(self, entry: dict, all_entries: list[dict]) -> dict:
        """
        Two-phase optimization for a single slide's image_width (w):

        Phase 1 — Satisfy the hard constraint f(w) = 0:
            If f > 0 (text is being clipped), shrink w by _step repeatedly
            until f reaches 0 or the lower bound (w>0) is hit.

        Phase 2 — Minimize empty space g(w):
            Starting from the w found in Phase 1 (where f=0), grow w by
            _step repeatedly. Accept only when f stays 0 AND g improves.
            Stop as soon as either condition fails.

        Both phases share the iteration budget SLIDE_IMPROVING_MAX_ITERATION.
        """
        args = entry["args"]
        slide_num = entry["slide_num"]

        w = float(args["image_width"].replace("%", ""))
        expected = self._get_expected_content(args)

        f_cur, g_cur = self._evaluate(entry, all_entries, slide_num, w, expected)
        logger.info(
            f"[SlideImproving] Slide {slide_num}: initial w={w:g}%  "
            f"f={f_cur:.4f}  g={g_cur:.4f}"
        )

        # ── Phase 1: shrink w until f == 0 ───────────────────────────────
        if f_cur > 0:
            logger.info(
                f"[SlideImproving] Slide {slide_num}: Phase 1 — shrinking to fit text "
                f"(f={f_cur:.4f})"
            )
            for it in range(1, self.SLIDE_IMPROVING_MAX_ITERATION + 1):
                cand_w = w - self._step
                if cand_w <= 0:
                    logger.info(
                        f"[SlideImproving] Slide {slide_num}: Phase 1 iter {it} — "
                        f"hit lower bound, stopping."
                    )
                    break

                c_f, c_g = self._evaluate(entry, all_entries, slide_num, cand_w, expected)
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: Phase 1 iter {it}  "
                    f"w={w:g}% -> {cand_w:g}%  f={c_f:.4f}  g={c_g:.4f}"
                )
                w, f_cur, g_cur = cand_w, c_f, c_g

                if f_cur == 0.0:
                    logger.info(
                        f"[SlideImproving] Slide {slide_num}: Phase 1 — "
                        f"f=0 reached at w={w:g}%"
                    )
                    break

            if f_cur > 0:
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: Phase 1 — "
                    f"could not reach f=0, keeping w={w:g}% (f={f_cur:.4f})"
                )
                new_args = {**args, "image_width": f"{w:g}%"}
                return {**entry, "args": new_args}

        # ── Phase 2: grow w to minimize g while f stays 0 ────────────────
        # Second-min safety margin: only step back to prev_w when the loop
        # stopped because f > 0 at the candidate (text was visually clipped).
        # In all other cases (g plateau, upper bound, exhausted iterations),
        # the accepted w already has the minimum g and is safe — use it directly.
        logger.info(
            f"[SlideImproving] Slide {slide_num}: Phase 2 — growing to fill space "
            f"(g={g_cur:.4f})"
        )
        prev_w, prev_f, prev_g = w, f_cur, g_cur   # fallback if f is violated
        stop_reason = "none"

        for it in range(1, self.SLIDE_IMPROVING_MAX_ITERATION + 1):
            cand_w = w + self._step
            if cand_w >= 100:
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: Phase 2 iter {it} — "
                    f"hit upper bound, stopping."
                )
                stop_reason = "upper_bound"
                break

            c_f, c_g = self._evaluate(entry, all_entries, slide_num, cand_w, expected)
            logger.info(
                f"[SlideImproving] Slide {slide_num}: Phase 2 iter {it}  "
                f"w={w:g}% -> {cand_w:g}%  f={c_f:.4f}  g={c_g:.4f}"
            )

            if c_f > 0:
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: Phase 2 iter {it} — "
                    f"f became {c_f:.4f} > 0, stopping."
                )
                stop_reason = "f_violated"
                break

            if c_g >= g_cur:
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: Phase 2 iter {it} — "
                    f"g did not improve ({c_g:.4f} >= {g_cur:.4f}), stopping."
                )
                stop_reason = "g_plateau"
                break

            # Accept step: save current as second-minimum before advancing
            prev_w, prev_f, prev_g = w, f_cur, g_cur
            w, f_cur, g_cur = cand_w, c_f, c_g

        # Only apply second-min (step back) when f was violated at the candidate.
        # prev_w < w in that case → safe margin without wasting space.
        # In all other cases, w already has the best (minimum) g — use it.
        if stop_reason == "f_violated" and prev_w < w:
            logger.info(
                f"[SlideImproving] Slide {slide_num}: f violated at w={w:g}% — "
                f"stepping back to second-min w={prev_w:g}% (g={prev_g:.4f}) for safety"
            )
            final_w = prev_w
        else:
            logger.info(
                f"[SlideImproving] Slide {slide_num}: stop_reason='{stop_reason}' — "
                f"using best w={w:g}% (g={g_cur:.4f})"
            )
            final_w = w

        new_args = {**args, "image_width": f"{final_w:g}%"}
        return {**entry, "args": new_args}

    def _evaluate(
        self,
        entry: dict,
        all_entries: list[dict],
        slide_num: int,
        w: float,
        expected: str,
    ) -> tuple[float, float]:
        """
        Render the slide with image_width=w%, then compute f(w) and g(w).

        Returns:
            (f, g)  both in [0, 1]
        """
        # Temporarily set w in the entry and regenerate .md
        tmp_args = {**entry["args"], "image_width": f"{w:g}%"}
        tmp_entry = {**entry, "args": tmp_args}
        tmp_entries = [tmp_entry if e["slide_num"] == slide_num else e for e in all_entries]
        self._replay_layouts(tmp_entries)

        # Export only this slide (overwrites {lecture_id}-export.pdf)
        self._export_pdf_single(slide_num)

        # Extract text with PyMuPDF
        extracted = self._extract_text_pymupdf()
        fuzzy_score = fuzzy_distance(expected, extracted)
        f = 1.0 - fuzzy_score / 100.0

        # Compute g: fraction of bg-coloured pixels in the rendered slide
        g = self._compute_bg_ratio()

        return f, g

    def _extract_text_pymupdf(self) -> str:
        """Extract all visible text from the single-page exported PDF using PyMuPDF."""
        pdf_path = self.slidev_dir / f"{self.lecture_id}-export.pdf"
        try:
            doc = fitz.open(str(pdf_path))
            text = doc[0].get_text("text")
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error(f"[SlideImproving] PyMuPDF text extraction failed: {e}")
            return ""

    def _compute_bg_ratio(self) -> float:
        """
        Fraction of pixels whose RGB distance to self._bg_color is < 25.
        Returns a value in [0, 1].
        """
        pdf_path = self.slidev_dir / f"{self.lecture_id}-export.pdf"
        try:
            doc = fitz.open(str(pdf_path))
            page = doc[0]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            doc.close()
        except Exception as e:
            logger.error(f"[SlideImproving] PDF→image failed for bg_ratio: {e}")
            return 0.0

        arr = np.array(img).astype(float)
        dist = np.linalg.norm(arr - self._bg_color, axis=2)
        bg_mask = dist < 25          # pixel is "background"
        ratio = float(np.mean(bg_mask))
        return ratio



    @staticmethod
    def _get_expected_content(args: dict) -> str:
        parts: list[str] = []
        for key in ("title", "sub_title_1", "sub_title_2"):
            if key in args and args[key]:
                parts.append(str(args[key]))
        for key in ("content", "toc_content", "sub_content_1", "sub_content_2"):
            val = args.get(key)
            if isinstance(val, list):
                parts.extend(str(v) for v in val)
            elif val:
                parts.append(str(val))
        if "latex_formula_block" in args:
            parts.append(str(args["latex_formula_block"]))
        if "caption" in args:
            parts.append(str(args["caption"]))
        if "caption1" in args and "caption2" in args:
            parts.append(str(args["caption1"]))
            parts.append(str(args["caption2"]))
        return " ".join(parts)

    def _read_layout_dist(self) -> list[dict]:
        with open(self.layout_dist_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_layout_dist(self, entries: list[dict]) -> None:
        with open(self.layout_dist_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def _replay_layouts(self, entries: list[dict]) -> None:
        from src.generator.slide_layout_manager import SlideLayoutManager

        mgr = SlideLayoutManager(
            theme=self.theme,
            font_sans=self.font,
            font_serif=self.font,
            font_mono=self.font,
            title=self.lecture_title,
            author=self.speaker_information,
        )
        doc = ""
        for entry in entries:
            func_name = entry["layout_function_name"]
            args = entry["args"]
            func = getattr(mgr, func_name)
            doc += func(**args)

        self.md_path.write_text(doc, encoding="utf-8")

    def _export_pdf_single(self, slide_num: int) -> None:
        """
        Export a single slide (1-indexed) to {lecture_id}-export.pdf.
        Uses --range {slide_num} --per-slide so only that page is written.
        The file is overwritten on every call.
        """
        cmd = (
            f'slidev export "{self.lecture_id}.md" '
            f"--range {slide_num} --per-slide"
        )
        logger.info(f"[SlideImproving] Exporting slide {slide_num}: {cmd}")
        _env = os.environ.copy()
        _env["NODE_OPTIONS"] = "--max-old-space-size=4096"
        result = subprocess.run(
            ["npm", "exec", "-c", cmd],
            cwd=str(self.slidev_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            env=_env,
        )
        if result.returncode != 0:
            logger.error(f"[SlideImproving] slidev export (single) failed:\n{result.stderr}")
            raise RuntimeError(f"slidev export failed: {result.stderr}")

    def _export_pdf_full(self) -> None:
        """Export the complete slide deck to {lecture_id}-export.pdf."""
        cmd = f'slidev export "{self.lecture_id}.md"'
        logger.info(f"[SlideImproving] Full export: {cmd}")
        _env = os.environ.copy()
        _env["NODE_OPTIONS"] = "--max-old-space-size=4096"
        result = subprocess.run(
            ["npm", "exec", "-c", cmd],
            cwd=str(self.slidev_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            env=_env,
        )
        if result.returncode != 0:
            logger.error(f"[SlideImproving] slidev export (full) failed:\n{result.stderr}")
            raise RuntimeError(f"slidev export failed: {result.stderr}")
        logger.info("[SlideImproving] Full export complete.")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(
        description="Optimise image_width per slide using PyMuPDF + bg-ratio objective."
    )
    parser.add_argument("md_path", help="Path to the .md slide file")
    parser.add_argument("--lecture-json", required=True, help="Path to lecture JSON file")
    parser.add_argument("--title", default="", help="Lecture title")
    parser.add_argument("--speaker", default="", help="Speaker information")
    args = parser.parse_args()

    improver = SlideImproving(
        md_path=args.md_path,
        lecture_json_path=args.lecture_json,
        lecture_title=args.title,
        speaker_information=args.speaker,
    )
    improver.run()
