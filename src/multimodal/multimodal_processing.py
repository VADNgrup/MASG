import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

from src.multimodal.graph import create_multimodal_workflow
from src.utils.file_utils import save_json


def _extract_lecture_id(lecture_path: Path, lecture_dict: dict) -> str:
    return lecture_dict.get("lecture_id") or lecture_path.stem

def multimodal_processing(lecture_path, output_path):
    # Load lecture JSON to extract lecture_id
    with open(lecture_path, "r", encoding="utf-8") as f:
        lecture_dict = json.load(f)

    lecture_id = _extract_lecture_id(lecture_path, lecture_dict)

    print(f"\n{'='*60}")
    print(f"Phase 3: Multimodal Processing")
    print(f"{'='*60}\n")
    print(f"Lecture ID : {lecture_id}")
    print(f"Lecture    : {lecture_path}")
    print(f"Slides     : {lecture_dict.get('metadata', {}).get('total_slides', 'N/A')}\n")

    initial_state = {
        "lecture_id": lecture_id,
        "used_images": set(),
        "used_tables": set(),
    }

    print("Creating multimodal workflow...")
    workflow = create_multimodal_workflow()

    print("Executing multimodal workflow...\n")
    result = workflow.invoke(initial_state)

    image_distributions  = result.get("image_distributions", [])
    table_distributions  = result.get("table_distributions", [])

    # Build lookup: slide_number → assets
    image_by_slide: dict = {}
    for dist in image_distributions:
        sn = dist.get("slide_number")
        if sn is not None:
            image_by_slide[sn] = dist

    table_by_slide: dict = {}
    for dist in table_distributions:
        sn = dist.get("slide_number")
        if sn is not None:
            table_by_slide[sn] = dist

    # Attach to each slide in lecture_dict
    for slide in lecture_dict.get("slides", []):
        sn = slide.get("slide_number")
        if sn in image_by_slide:
            slide["image"] = image_by_slide[sn]
        if sn in table_by_slide:
            slide["table"] = table_by_slide[sn]

    # Add multimodal metadata
    lecture_dict["multimodal"] = {
        "processed_at": datetime.now().isoformat(),
        "total_image_distributions": len(image_distributions),
        "total_table_distributions": len(table_distributions),
        "aggregated_media_summary": {
            "total_images": result.get("aggregated_media", {}).get("total_images", 0),
            "total_tables": result.get("aggregated_media", {}).get("total_tables", 0),
        },
    }

    # Determine output path
    if not output_path:
        output_path = lecture_path.parent / f"{lecture_id}_multimodal.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(lecture_dict, output_path)

    print(f"\n{'='*60}")
    print(f"Multimodal Processing Completed")
    print(f"{'='*60}\n")
    print(f"Output             : {output_path}")
    print(f"Distributed Images : {len(image_distributions)}")
    print(f"Distributed Tables : {len(table_distributions)}")
    print(f"Available Images   : {result.get('aggregated_media', {}).get('total_images', 0)}")
    print(f"Available Tables   : {result.get('aggregated_media', {}).get('total_tables', 0)}")
    print(f"\n{'='*60}")
    print(f"End Phase 3: Multimodal Processing")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3: Multimodal Processing — distribute images & tables to slides"
    )
    parser.add_argument(
        "--lecture",
        required=True,
        help="Path to lecture JSON file (e.g. data/lectures/lec_6895e38a.json)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (default: same dir as input, with _multimodal suffix)",
    )
    args = parser.parse_args()

    lecture_path = Path(args.lecture)
    output_path = args.output
    if not lecture_path.exists():
        raise FileNotFoundError(f"Lecture file not found: {lecture_path}")
    else:
        multimodal_processing(lecture_path, output_path)

if __name__ == "__main__":
    main()
