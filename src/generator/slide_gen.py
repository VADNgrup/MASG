from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys

import fitz  # PyMuPDF
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.generator.slide_pick_and_merge import SlidePickMerge
from src.generator.slide_improving import SlideImproving
from src.utils.config import Config

logger = logging.getLogger(__name__)


def _load_lecture_meta(json_path: Path) -> tuple[str, str]:
    
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else {}

    if not isinstance(data, dict):
        return json_path.stem, json_path.stem

    lecture_id: str = data.get("lecture_id", json_path.stem)
    title: str = data.get("title") or data.get("lecture_title") or lecture_id

    return title, lecture_id


def run_pipeline(
    lecture_json_path: str,
    lecture_title: str | None = None,
    speaker_information: str = "",
) -> None:
    """
    Full end-to-end pipeline:
      1. Build initial Slidev markdown from the lecture JSON.
      2. Evaluate and iteratively improve via per-slide optimization.
      --lecture   PATH    Json lecture PATH
      --title     STR     Override lecture title (default: from JSON or lecture_id)
      --speaker   STR     Speaker information
      --log-level LEVEL   DEBUG / INFO / WARNING / ERROR

    """
    json_path = Path(lecture_json_path).resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"Lecture JSON not found: {json_path}")

    inferred_title, lecture_id = _load_lecture_meta(json_path)
    title = lecture_title or inferred_title

    print(f"\n{'='*60}")
    print(f"Phase 4: Slide Generation")
    print(f"{'='*60}\n")

    print(f"[slide_gen] Lecture  : {lecture_id}")
    print(f"[slide_gen] Title    : {title}")
    print(f"[slide_gen] Speaker  : {speaker_information or 'Slide Generation System'}")

    slidev_dir = _PROJECT_ROOT / "src" / "generator" / "slidev"
    md_path = slidev_dir / f"{lecture_id}.md"

    model_name = (Config.LLM_MODEL_NAME or "unknown_model").replace("/", "_")
    out_pdf_path = _PROJECT_ROOT / "output" / lecture_id / model_name / f"{lecture_id}-export.pdf"

    if out_pdf_path.exists():
        print(f"[slide_gen] Output PDF already exists, skipping build & improve: {out_pdf_path}")
        print(f"\n{'='*60}")
        print(f"End Phase 4: Slide already packaged at {out_pdf_path}")
        print(f"{'='*60}\n")
        return
    else:
        print("[slide_gen] === Step 1: Building slide layout ===")
        if not title:
            title = json.load(json_path)["lecture_title"]
        picker = SlidePickMerge(
            lecture_json_path=str(json_path),
            lecture_title=title,
            speaker_information=speaker_information,
        )
        picker.build()
        selected_theme = picker.theme
        selected_font = picker.font

        print("[slide_gen] === Step 2: Evaluating and improving slides ===")

        improver = SlideImproving(
            md_path=str(md_path),
            lecture_json_path=str(json_path),
            lecture_title=title,
            speaker_information=speaker_information,
            theme=selected_theme,
            font=selected_font,
        )
        improver.run()

        print(f"\n{'='*60}")
        print(f"End Phase 4: Generated Slide in {md_path}")
        print(f"{'='*60}\n")

    # Package output: PDF + JSON + slide images
    _package_output(
        lecture_id=lecture_id,
        slidev_dir=slidev_dir,
        lecture_json_path=json_path,
    )


def _package_output(
    lecture_id: str,
    slidev_dir: Path,
    lecture_json_path: Path,
) -> None:
    """
    After the final PDF export:
      1. Create  output/{lecture_id}/{model_name}/
      2. Move/copy  {lecture_id}-export.pdf  and  {lecture_id}.json  there.
      3. Create  output/{lecture_id}/{model_name}/slide_images/
         and render every PDF page to  slide_0001.jpg, slide_0002.jpg, …
    If the destination directory already exists:
      - clear slide_images/ only
      - overwrite the PDF and JSON files
    """
    from src.utils.config import Config

    model_name = (Config.LLM_MODEL_NAME or "unknown_model").replace("/", "_")

    out_dir = _PROJECT_ROOT / "output" / lecture_id / model_name
    images_dir = out_dir / "slide_images"

    # prepare directories
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    # move PDF
    pdf_src = slidev_dir / f"{lecture_id}-export.pdf"
    if not pdf_src.exists():
        raise FileNotFoundError(f"[package_output] PDF not found: {pdf_src}")
    pdf_dst = out_dir / f"{lecture_id}-export.pdf"
    shutil.move(str(pdf_src), pdf_dst)
    print(f"[package_output] PDF moved → {pdf_dst}")

    # copy JSON
    json_dst = out_dir / lecture_json_path.name
    shutil.copy2(lecture_json_path, json_dst)
    print(f"[package_output] JSON copied → {json_dst}")

    # copy table_distribution and image_distribution (optional siblings)
    for suffix in ("_table_distribution", "_image_distribution"):
        sibling = lecture_json_path.parent / f"{lecture_id}{suffix}.json"
        if sibling.exists():
            shutil.copy2(sibling, out_dir / sibling.name)
            print(f"[package_output] JSON copied → {out_dir / sibling.name}")
        else:
            print(f"[package_output] (skipped, not found) {sibling.name}")

    # render PDF pages to JPEG images
    doc = fitz.open(str(pdf_dst))
    page_count = len(doc)
    for page_num in range(page_count):
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)  # 2× scale for quality
        pix = page.get_pixmap(matrix=mat)
        img_name = f"slide_{page_num + 1:04d}.jpg"
        pix.save(str(images_dir / img_name))
    doc.close()
    print(f"[package_output] {page_count} slide image(s) saved → {images_dir}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.generator.slide_gen",
        description=(
            "End-to-end slide generation pipeline.\n"
            "Reads a lecture JSON, generates a Slidev markdown, then "
            "evaluates and improves the slides using a VLM/LLM loop."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lecture",
        required=True,
        metavar="PATH",
        help=(
            "Path to the lecture JSON file, e.g. "
            "data/lectures/lec_6895e38a.json"
        ),
    )
    parser.add_argument(
        "--title",
        default=None,
        metavar="STR",
        help=(
            "Override the lecture title shown on the slides. "
            "If omitted, the value from the JSON (key 'title' or 'lecture_id') is used."
        ),
    )
    parser.add_argument(
        "--speaker",
        default="Slidev with Slide Generation System",
        metavar="STR",
        help="Speaker / author information shown on greeting and goodbye slides.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    run_pipeline(
        lecture_json_path=args.lecture,
        lecture_title=args.title,
        speaker_information=args.speaker,
    )
