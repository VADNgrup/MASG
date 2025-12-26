import json
from pathlib import Path

json_path = "data/lectures/lec_980a509f.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

slides_data = data.get("slides", [])
json_file = Path(json_path)
lecture_id = json_file.stem.replace("lec_", "")

print(f"Lecture ID: {lecture_id}")

assets_source = Path("data/assets") / lecture_id / "images"
print(f"Assets source: {assets_source}")
print(f"Assets source exists: {assets_source.exists()}")

image_ids = set()
for i, slide in enumerate(slides_data):
    image_data = slide.get("image")
    if isinstance(image_data, dict):
        image_id = image_data.get("image_id")
        if image_id:
            image_ids.add(image_id)
            print(f"Slide {i}: Found image_id = {image_id}")

print(f"\nTotal image_ids: {len(image_ids)}")
print(f"Image IDs: {image_ids}")

if assets_source.exists():
    print(f"\nLooking for images in: {assets_source}")
    for image_id in image_ids:
        for ext in ['.png', '.jpg', '.jpeg']:
            src_file = assets_source / f"{image_id}{ext}"
            print(f"  Checking: {src_file} -> exists: {src_file.exists()}")
            if src_file.exists():
                print(f"    FOUND: {src_file}")
                break
