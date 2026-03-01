"""
SlideImproving - VLM-based slide quality evaluator and auto-refiner.

Workflow:
1. Export the .md file via `slidev export` → PDF
2. Convert PDF pages to images in memory
3. Send each image to a VLM for scoring/feedback
4. If average score < 7, apply LLM-based refinements and repeat (max 3 rounds)
5. Save the best-scoring .md as the final slidev/{lecture_id}.md and export its PDF
"""

import os
import sys
import json
import base64
import shutil
import logging
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from openai import OpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve project root so that `llm_extension` can be imported regardless of
# the working directory from which this module is used.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# VLM evaluation prompt
# ---------------------------------------------------------------------------
_EVAL_SYSTEM_PROMPT = """\
Bạn là một designer chuyên nghiệp, chuyên đánh giá những slide thuyết trình một cách khắt khe và khó tính nhất. Bạn luôn có tiêu chuẩn về slide cao, không chấp nhận bất cứ slide nào kém chất lượng.
Hãy phân tích ảnh slide được cung cấp và trả về JSON với đúng định dạng sau (không thêm bất cứ thứ gì khác):
{
  "slide_num": <số thứ tự slide>,
  "text": "<văn bản quá dài, hoặc 'không vấn đề'>",
  "image": "<hình ảnh quá lớn/nhỏ, hoặc 'không vấn đề'>",
  "score": <điểm chất lượng từ 1 đến 10>
  "title_color_suggestion": "<màu sắc gợi ý cho title>",
  "font_name_suggestion": <kích thước font gợi ý>, dựa theo Google Fonts.
}
"""

# ---------------------------------------------------------------------------
# LLM improvement prompt
# ---------------------------------------------------------------------------
_IMPROVE_SYSTEM_PROMPT = """\
Bạn là chuyên gia chỉnh sửa nội dung slide Slidev (Markdown).
Nhiệm vụ của bạn là chỉnh sửa file Markdown Slidev dựa trên phản hồi từ VLM.

Quy tắc QUAN TRỌNG:
- Chỉ sửa những slide có feedback chỉ rõ vấn đề (text hoặc image khác "không vấn đề").
- Với vấn đề chữ bị tràn / quá nhiều chữ: rút gọn nội dung text của slide đó.
- Với vấn đề ảnh quá bé: tăng imageWidth của thẻ <img> hoặc thuộc tính width trong markdown. \
Nếu chưa có imageWidth thì thêm vào, ví dụ: <img src="..." imageWidth="500" />
- KHÔNG thay đổi cấu trúc YAML frontmatter, layout, separator (---), hoặc các slide không có feedback.
- KHÔNG thêm slide mới hoặc xoá slide.
- Đối với các feedback về title_color_suggestion, hãy lấy màu nào mà có thể trung hòa tất cả các ý kiến của mỗi slide. Màu của Title ở thẻ <h1 style="color:;">. Lưu ý tất cả title phải thống nhất sử dụng 1 màu duy nhất 
- Đối với các feedback về font_name_suggestion, hãy lấy font nào mà có thể trung hòa tất cả các ý kiến của mỗi slide. Font được chỉnh sửa ở phần đầu của file markdown.
- Trả về NỘI DUNG FILE MARKDOWN ĐẦY ĐỦ, không thêm markdown fences (```).
"""


class SlideImproving:
    """
    Evaluate and iteratively improve a Slidev markdown file using a VLM.

    Parameters
    ----------
    md_path : str
        Path to the source `.md` file, e.g. ``slidev/lec_abc123.md``.
    max_iterations : int
        Maximum improvement cycles (default 3).
    pass_threshold : float
        Average score threshold above which no changes are made (default 7.0).
    """

    def __init__(
        self,
        md_path: str,
        max_iterations: int = 3,
        pass_threshold: float = 8.5,
    ):
        # Resolve path: try as-given first, then relative to src/generator/
        _given = Path(md_path)
        _generator_dir = Path(__file__).parent   # .../src/generator
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
        self.lecture_id = self.md_path.stem          # e.g. "lec_abc123"
        self.max_iterations = max_iterations
        self.pass_threshold = pass_threshold

        # VLM client (reads config from environment via src/utils/config.py)
        from src.utils.config import Config
        self._vlm_client = OpenAI(
            api_key=Config.VLM_API_KEY,
            base_url=Config.VLM_BASE_URL,
        )
        self._vlm_model = Config.VLM_MODEL_NAME

        # Best-score tracking
        self._best_score: float = -1.0
        self._best_md_tmp: Optional[Path] = None   # temp copy in slidev dir
        self._tmp_files: list[Path] = []            # all temp files to clean up

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run the full evaluation + improvement loop."""
        logger.info(f"[SlideImproving] Starting for lecture '{self.lecture_id}'")

        try:
            for iteration in range(1, self.max_iterations + 1):
                logger.info(f"[SlideImproving] === Iteration {iteration}/{self.max_iterations} ===")

                # 1. Export PDF
                self._export_pdf()

                # 2. Convert PDF to images
                images = self._pdf_to_images()
                if not images:
                    logger.warning("[SlideImproving] No images extracted from PDF. Stopping.")
                    break

                # 3. Evaluate each slide
                feedback = self._evaluate_slides(images)
                avg_score = sum(f["score"] for f in feedback) / len(feedback)
                logger.info(
                    f"[SlideImproving] Average score: {avg_score:.2f} "
                    f"(threshold: {self.pass_threshold})"
                )

                # 4. Track best version
                if avg_score > self._best_score:
                    self._best_score = avg_score
                    self._save_best_copy()

                # 5. Stop if quality is sufficient
                if avg_score >= self.pass_threshold:
                    logger.info(
                        f"[SlideImproving] Quality threshold met "
                        f"({avg_score:.2f} >= {self.pass_threshold}). Done."
                    )
                    break

                # 6. If last iteration, stop improving (will restore best below)
                if iteration == self.max_iterations:
                    logger.info(
                        "[SlideImproving] Max iterations reached without meeting threshold."
                    )
                    break

                # 7. Improve the markdown
                logger.info("[SlideImproving] Applying LLM-based improvements …")
                self._improve_markdown(feedback)

        finally:
            # Restore best version if it was saved
            self._restore_best_if_needed()
            # Final export with the winning .md
            self._export_pdf()
            # Cleanup temp files
            self._cleanup_tmp_files()

        logger.info("[SlideImproving] Finished.")

    # ------------------------------------------------------------------
    # Step 1: Export PDF
    # ------------------------------------------------------------------

    def _export_pdf(self) -> None:
        """Run `slidev export` in the slidev directory."""
        cmd = f'slidev export "{self.lecture_id}.md"'
        logger.info(f"[SlideImproving] Running: npm exec -c '{cmd}' in {self.slidev_dir}")
        result = subprocess.run(
            ["npm", "exec", "-c", cmd],
            cwd=str(self.slidev_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",     # explicit UTF-8 to avoid cp1252 issues on Windows
            errors="replace",     # replace undecodable bytes instead of raising
            shell=True,           # required on Windows for npm shims
        )
        if result.returncode != 0:
            logger.error(f"[SlideImproving] slidev export failed:\n{result.stderr}")
            raise RuntimeError(f"slidev export failed: {result.stderr}")
        logger.info("[SlideImproving] Export complete.")

    # ------------------------------------------------------------------
    # Step 2: PDF → images (in memory)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Step 3: Evaluate slides via VLM
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_vlm_json(raw: str, slide_num: int) -> dict:
        """
        Robustly extract JSON from VLM output that may contain surrounding text,
        markdown fences, or trailing think-tags used by some models.
        """
        import re
        # 1. Strip <think>…</think> blocks (Qwen-style)
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # 2. Strip markdown fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
            raw = raw.rstrip("`").strip()
        # 3. Try direct parse
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        # 4. Try extracting the first {...} block
        match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Cannot parse VLM response for slide {slide_num}: {raw!r}")

    def _evaluate_slides(self, images: list[bytes]) -> list[dict]:
        """Send each slide image to the VLM and collect feedback."""
        feedback: list[dict] = []
        for idx, img_bytes in enumerate(images, start=1):
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            try:
                response = self._vlm_client.chat.completions.create(
                    model=self._vlm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": _EVAL_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Đây là slide số {idx}. Hãy đánh giá.",
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
                    temperature=0.2,
                )
                raw = response.choices[0].message.content.strip()
                fb = self._parse_vlm_json(raw, idx)
                fb["slide_num"] = idx   # always set from our counter
                feedback.append(fb)
                logger.info(
                    f"[SlideImproving] Slide {idx} feedback:\n"
                    + json.dumps(fb, ensure_ascii=False, indent=2)
                )
            except Exception as e:
                logger.error(
                    f"[SlideImproving] Error evaluating slide {idx}: {e}. "
                    f"Raw response: {locals().get('raw', '(no response)')!r}"
                )
                feedback.append({
                    "slide_num": idx,
                    "text": "không thể đánh giá",
                    "image": "không thể đánh giá",
                    "score": 5,
                })
        return feedback

    # ------------------------------------------------------------------
    # Step 4: Improve markdown via LLM
    # ------------------------------------------------------------------

    def _improve_markdown(self, feedback: list[dict]) -> None:
        """Use ChatLLM (via llm_extension) to refine the markdown file."""
        import llm_extension  # noqa: F401 – patches openai / langchain
        from llm_extension.llm_langchain import ChatLLM
        from langchain_core.messages import HumanMessage, SystemMessage

        current_md = self.md_path.read_text(encoding="utf-8")
        feedback_json = json.dumps(feedback, ensure_ascii=False, indent=2)

        llm = ChatLLM(model="qwen3-30b-a3b", temperature=0.3)

        messages = [
            SystemMessage(content=_IMPROVE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Đây là nội dung file Markdown hiện tại:\n\n"
                    f"{current_md}\n\n"
                    f"---\n\n"
                    f"Đây là phản hồi từ VLM (JSON):\n\n"
                    f"{feedback_json}\n\n"
                    f"Hãy trả về file Markdown đã được cải thiện."
                )
            ),
        ]

        response = llm.invoke(messages)
        improved_md = response.content.strip()
        # Strip possible markdown fences from response
        if improved_md.startswith("```"):
            lines = improved_md.split("\n")
            improved_md = "\n".join(lines[1:]).rstrip("`").strip()

        self.md_path.write_text(improved_md, encoding="utf-8")
        logger.info(f"[SlideImproving] Markdown updated at {self.md_path}")

    # ------------------------------------------------------------------
    # Best-version bookkeeping
    # ------------------------------------------------------------------

    def _save_best_copy(self) -> None:
        """Save the current .md as a temp file (best so far)."""
        # Remove old best copy
        if self._best_md_tmp and self._best_md_tmp.exists():
            self._best_md_tmp.unlink(missing_ok=True)

        tmp_name = f"_best_{self.lecture_id}.md"
        tmp_path = self.slidev_dir / tmp_name
        shutil.copy2(self.md_path, tmp_path)
        self._best_md_tmp = tmp_path
        if tmp_path not in self._tmp_files:
            self._tmp_files.append(tmp_path)
        logger.info(f"[SlideImproving] Saved best copy → {tmp_path} (score={self._best_score:.2f})")

    def _restore_best_if_needed(self) -> None:
        """If the current .md is not the best, restore the best version."""
        if self._best_md_tmp and self._best_md_tmp.exists():
            shutil.copy2(self._best_md_tmp, self.md_path)
            logger.info(
                f"[SlideImproving] Restored best .md "
                f"(score={self._best_score:.2f}) → {self.md_path}"
            )

    def _cleanup_tmp_files(self) -> None:
        """Delete all temporary files created during the process."""
        for tmp in self._tmp_files:
            try:
                if tmp.exists():
                    tmp.unlink()
                    logger.info(f"[SlideImproving] Deleted temp file: {tmp}")
            except Exception as e:
                logger.warning(f"[SlideImproving] Could not delete {tmp}: {e}")
        self._tmp_files.clear()


# ---------------------------------------------------------------------------
# Quick CLI usage: python -m src.generator.slide_improving slidev/lec_xxx.md
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate and improve a Slidev .md file.\n"
            "Path can be relative to cwd or to src/generator/ — e.g. slidev/lec_xxx.md"
        )
    )
    parser.add_argument("md_path", help="Path to the .md slide file, e.g. slidev/lec_xxx.md")
    parser.add_argument("--max-iter", type=int, default=3, help="Max improvement iterations")
    parser.add_argument("--threshold", type=float, default=8.5, help="Pass score threshold")
    args = parser.parse_args()

    improver = SlideImproving(
        md_path=args.md_path,
        max_iterations=args.max_iter,
        pass_threshold=args.threshold,
    )
    improver.run()
