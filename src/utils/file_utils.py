import json
from pathlib import Path
from typing import Any, Dict, Union

def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    file_path = Path(file_path)  # Convert to Path if string
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(file_path: Path) -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

