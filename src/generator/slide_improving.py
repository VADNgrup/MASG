import re
from src.utils.parse_llm_response import clear_think
import sys
import json
import base64
import logging
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
from openai import OpenAI
from src.utils.fuzzy_distance import fuzzy_distance

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_TEXT_EXTRACT_PROMPT = """\
Bạn là một OCR chuyên nghiệp. Hãy trích xuất TOÀN BỘ văn bản hiển thị trên slide này.
Trả về plaintext, mỗi dòng tương ứng với một dòng trên slide.
Không thêm giải thích, không thêm markdown formatting.
"""

_EMPTY_SPACE_PROMPT = """\
Bạn là một designer chuyên nghiệp. Hãy đánh giá diện tích trống trên slide này.
Chỉ trả về JSON đúng định dạng sau (không thêm bất cứ thứ gì khác):
{
  "issue": "<LARGE_EMPTY_SPACE hoặc MEDIUM_EMPTY_SPACE hoặc OK>"
}
Tiêu chí:
- LARGE_EMPTY_SPACE: slide có quá nhiều diện tích trống, ảnh quá nhỏ so với không gian slide, hoặc chữ quá ít.
- MEDIUM_EMPTY_SPACE: slide có một phần diện tích trống đáng kể nhưng không quá nghiêm trọng.
- OK: slide sử dụng không gian hợp lý, cân đối giữa nội dung và khoảng trống.
"""

TWO_IMAGE_MAX_LEFT_RIGHT_WIDTH = 20
TWO_IMAGE_MIN_LEFT_RIGHT_WIDTH = 25
ONE_IMAGE_MAX_LEFT_RIGHT_WIDTH = 45
ONE_IMAGE_MIN_LEFT_RIGHT_WIDTH = 30
TWO_IMAGE_MAX_ABOVE_BELOW_WIDTH = 70
TWO_IMAGE_MIN_ABOVE_BELOW_WIDTH = 50
ONE_IMAGE_MAX_ABOVE_BELOW_WIDTH = 70
ONE_IMAGE_MIN_ABOVE_BELOW_WIDTH = 50


class SlideImproving:
    def __init__(
        self,
        md_path: str,
        lecture_json_path: str,
        lecture_title: str = "",
        speaker_information: str = "",
        max_iterations: int = 3,
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
        self.max_iterations = max_iterations
        self.theme = theme
        self.font = font

        # Layout distribution path (same dir as lecture JSON)
        _lec_json = Path(lecture_json_path).resolve()
        self.layout_dist_path = _lec_json.parent / f"{self.lecture_id}_layout_distribution.json"

        # For replaying layouts
        self.lecture_title = lecture_title
        self.speaker_information = speaker_information

        # VLM client
        from src.utils.config import Config
        self._vlm_client = OpenAI(
            api_key=Config.VLM_API_KEY,
            base_url=Config.VLM_BASE_URL,
        )
        self._vlm_model = Config.VLM_MODEL_NAME

    def run(self) -> None:
        logger.info(f"[SlideImproving] Starting for lecture '{self.lecture_id}'")

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"[SlideImproving] === Iteration {iteration}/{self.max_iterations} ===")

            # 1. Export PDF
            self._export_pdf()

            # 2. PDF → images
            images = self._pdf_to_images()
            if not images:
                logger.warning("[SlideImproving] No images extracted from PDF. Stopping.")
                break

            # 3. Read layout distribution
            entries = self._read_layout_dist()

            # 4. Evaluate and adjust
            updated_entries, changed = self._evaluate_and_adjust(entries, images)

            # 5. Write updated layout distribution
            self._write_layout_dist(updated_entries)

            # 6. Replay layouts → regenerate .md
            self._replay_layouts(updated_entries)

            if not changed:
                logger.info("[SlideImproving] No changes needed. Done.")
                break

        # Final export
        self._export_pdf()
        logger.info("[SlideImproving] Finished.")

    def _evaluate_and_adjust(
        self, entries: list[dict], images: list[bytes]
    ) -> tuple[list[dict], bool]:
        """Evaluate each slide and adjust image_width if needed."""
        updated: list[dict] = []
        changed = False

        for entry in entries:
            args = entry.get("args", {})
            slide_num = entry["slide_num"]
            # Skip slides without image_width
            if "image_width" not in args:
                updated.append(entry)
                continue
            two_image = "two_image" in entry.get("layout_function_name", "")
            layout_name = entry.get("layout_function_name", "")
            above_below = "above" in layout_name or "below" in layout_name
            image_width = float(args.get("image_width").replace("%", ""))

            # Determine min/max bounds based on layout type (4-way)
            if two_image and above_below:
                _max_w = TWO_IMAGE_MAX_ABOVE_BELOW_WIDTH
                _min_w = TWO_IMAGE_MIN_ABOVE_BELOW_WIDTH
            elif two_image:
                _max_w = TWO_IMAGE_MAX_LEFT_RIGHT_WIDTH
                _min_w = TWO_IMAGE_MIN_LEFT_RIGHT_WIDTH
            elif above_below:
                _max_w = ONE_IMAGE_MAX_ABOVE_BELOW_WIDTH
                _min_w = ONE_IMAGE_MIN_ABOVE_BELOW_WIDTH
            else:
                _max_w = ONE_IMAGE_MAX_LEFT_RIGHT_WIDTH
                _min_w = ONE_IMAGE_MIN_LEFT_RIGHT_WIDTH

            # Get corresponding slide image (slide_num is 1-indexed)
            img_idx = slide_num - 1
            if img_idx < 0 or img_idx >= len(images):
                logger.warning(
                    f"[SlideImproving] Slide {slide_num}: "
                    f"no image at index {img_idx} (total={len(images)}). Skipping."
                )
                updated.append(entry)
                continue

            img_bytes = images[img_idx]
            current_width = args["image_width"]
            delta = 0

            expected = self._get_expected_content(args)
            extracted = self._extract_text_vlm(img_bytes)
            score = fuzzy_distance(expected, extracted)
            logger.info(
                f"[SlideImproving] Slide {slide_num}: "
                f"fuzzy_score={score:.1f} (expected_len={len(expected)}, "
                f"extracted_len={len(extracted)})"
            )

            # Shrink deltas differ by layout type
            if two_image and not above_below:
                shrink_large, shrink_small = 2.5, 1.25
            else:
                shrink_large, shrink_small = 10, 5

            if score < 90:
                if image_width - shrink_large >= _min_w:
                    delta -= shrink_large
                else:
                    image_width = _min_w
            elif score < 95:
                if image_width - shrink_small >= _min_w:
                    delta -= shrink_small
                else:
                    image_width = _min_w

            if score >= 98:
                issue = self._evaluate_empty_space(img_bytes)
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: empty_space={issue}"
                )

                # Grow deltas differ by layout type
                if two_image and not above_below:
                    grow_large, grow_small = 1.25, 0.625
                else:
                    grow_large, grow_small = 10, 5

                if issue == "LARGE_EMPTY_SPACE":
                    if image_width + grow_large <= _max_w:
                        delta += grow_large
                    else:
                        image_width = _max_w
                elif issue == "MEDIUM_EMPTY_SPACE":
                    if image_width + grow_small <= _max_w:
                        delta += grow_small
                    else:
                        image_width = _max_w

            if delta != 0:
                new_width = self._adjust_image_width(current_width, delta)
                entry = {**entry, "args": {**args, "image_width": new_width}}
                changed = True
                logger.info(
                    f"[SlideImproving] Slide {slide_num}: "
                    f"{current_width} → {new_width} (delta={delta:+g}%)"
                )

            updated.append(entry)

        return updated, changed

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

    @staticmethod
    def _adjust_image_width(current: str, delta: float) -> str:
        """Adjust percentage width by delta. Clamp to [10%, 90%]."""
        val = float(current.replace("%", ""))
        val = max(10.0, min(90.0, val + delta))
        return f"{val:g}%"

    def _extract_text_vlm(self, img_bytes: bytes) -> str:
        """Send slide image to VLM and extract all visible text."""
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        try:
            response = self._vlm_client.chat.completions.create(
                model=self._vlm_model,
                messages=[
                    {"role": "system", "content": _TEXT_EXTRACT_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Trích xuất toàn bộ text trên slide này.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}",
                                },
                            },
                        ],
                    },
                ],
                temperature=0.1,
            )
            raw = clear_think(response.choices[0].message.content)
            return raw
        except Exception as e:
            logger.error(f"[SlideImproving] Text extraction failed: {e}")
            return ""

    def _evaluate_empty_space(self, img_bytes: bytes) -> str:
        """Send slide image to VLM and evaluate empty space."""
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        try:
            response = self._vlm_client.chat.completions.create(
                model=self._vlm_model,
                messages=[
                    {"role": "system", "content": _EMPTY_SPACE_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Đánh giá diện tích trống trên slide này.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}",
                                },
                            },
                        ],
                    },
                ],
                temperature=0.1,
            )
            raw = clear_think(response.choices[0].message.content)
            return self._parse_issue_json(raw)
        except Exception as e:
            logger.error(f"[SlideImproving] Empty space eval failed: {e}")
            return "OK"

    @staticmethod
    def _parse_issue_json(raw: str) -> str:
        """Parse {"issue": "..."} from VLM response."""
        # Strip markdown fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        try:
            return json.loads(raw).get("issue", "OK")
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group()).get("issue", "OK")
            except json.JSONDecodeError:
                pass
        # Fallback: keyword search
        if "LARGE_EMPTY_SPACE" in raw:
            return "LARGE_EMPTY_SPACE"
        if "MEDIUM_EMPTY_SPACE" in raw:
            return "MEDIUM_EMPTY_SPACE"
        return "OK"

    def _read_layout_dist(self) -> list[dict]:
        """Read layout distribution JSON."""
        with open(self.layout_dist_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_layout_dist(self, entries: list[dict]) -> None:
        """Write updated layout distribution JSON."""
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
        logger.info(f"[SlideImproving] Markdown replayed → {self.md_path}")

    def _export_pdf(self) -> None:
        """Run `slidev export` in the slidev directory."""
        cmd = f'slidev export "{self.lecture_id}.md"'
        logger.info(f"[SlideImproving] Running: npm exec -c '{cmd}' in {self.slidev_dir}")
        result = subprocess.run(
            ["npm", "exec", "-c", cmd],
            cwd=str(self.slidev_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
        )
        if result.returncode != 0:
            logger.error(f"[SlideImproving] slidev export failed:\n{result.stderr}")
            raise RuntimeError(f"slidev export failed: {result.stderr}")
        logger.info("[SlideImproving] Export complete.")

    def _pdf_to_images(self) -> list[bytes]:
        """Convert each PDF page to a PNG bytes object."""
        pdf_path = self.slidev_dir / f"{self.lecture_id}-export.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"Exported PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        images: list[bytes] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = fitz.Matrix(2, 2)   # 2× scale for better resolution
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        doc.close()
        logger.info(f"[SlideImproving] Extracted {len(images)} slide image(s) from PDF.")
        return images


if __name__ == "__main__":

    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(
        description="Evaluate and improve a Slidev .md file using layout distribution."
    )
    parser.add_argument("md_path", help="Path to the .md slide file")
    parser.add_argument("--lecture-json", required=True, help="Path to lecture JSON file")
    parser.add_argument("--title", default="", help="Lecture title")
    parser.add_argument("--speaker", default="", help="Speaker information")
    parser.add_argument("--max-iter", type=int, default=3, help="Max improvement iterations")
    args = parser.parse_args()

    improver = SlideImproving(
        md_path=args.md_path,
        lecture_json_path=args.lecture_json,
        lecture_title=args.title,
        speaker_information=args.speaker,
        max_iterations=args.max_iter,
    )
    improver.run()
