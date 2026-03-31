from __future__ import annotations

import argparse
import json
import logging
import sys

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
    max_iterations: int = 3
) -> None:
    """
    Full end-to-end pipeline:
      1. Build initial Slidev markdown from the lecture JSON.
      2. Evaluate and iteratively improve via VLM / LLM.
      --lecture   PATH    (bắt buộc) Đường dẫn tới file JSON
      --title     STR     Override tên bài giảng (mặc định: lấy từ JSON hoặc lecture_id)
      --speaker   STR     Thông tin người thuyết trình
      --max-iter  N       Số vòng cải thiện tối đa (mặc định: 3)
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
    print(f"[slide_gen] Speaker  : {speaker_information or '(not set)'}")

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

    slidev_dir = _PROJECT_ROOT / "src" / "generator" / "slidev"

    print("[slide_gen] === Step 2: Evaluating and improving slides ===")

    md_path = slidev_dir / f"{lecture_id}.md"
    improver = SlideImproving(
        md_path=str(md_path),
        lecture_json_path=str(json_path),
        lecture_title=title,
        speaker_information=speaker_information,
        max_iterations=max_iterations,
        theme=selected_theme,
        font=selected_font,
    )
    improver.run()

    print(f"\n{'='*60}")
    print(f"End Phase 4: Generated Slide in {md_path}")
    print(f"{'='*60}\n")


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
        max_iterations=Config.SLIDE_ITERATION_NUMBER
    )
