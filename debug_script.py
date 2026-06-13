import json
from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_PROJECT_ROOT))
from src.generator.slide_pick_and_merge import SlidePickMerge

def debug():
    json_path = _PROJECT_ROOT / 'output/TinyChart/gpt-4.1-mini/TinyChart.json'
    picker = SlidePickMerge(
        lecture_json_path=str(json_path),
        lecture_title="TinyChart",
        speaker_information="",
        deck_dir=_PROJECT_ROOT / 'output/debug'
    )
    print("Loaded image dist:", picker._image_dist)
    
debug()
