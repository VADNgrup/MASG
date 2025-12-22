ICON_MAP = {
    "definition": "rotate-360",
    "key_concept": "rotate-360",
    "formula": "function",
    "example": "chart-line-data",
    "property": "concept",
    "note": "idea",
    "important": "warning-alt",
    "warning": "warning-alt",
    "other": "concept"
}

COLOR_MAP = {
    "definition": {"bg": "bg-blue-50", "border": "border-blue-500", "text": "text-blue-700"},
    "key_concept": {"bg": "bg-blue-50", "border": "border-blue-500", "text": "text-blue-700"},
    "formula": {"bg": "bg-gradient-to-br from-blue-100 to-purple-100", "border": "", "text": "text-blue-700"},
    "example": {"bg": "bg-gradient-to-br from-purple-100 to-pink-100", "border": "", "text": "text-purple-700"},
    "property": {"bg": "bg-green-50", "border": "border-green-500", "text": "text-green-700"},
    "note": {"bg": "bg-gray-50", "border": "border-gray-400", "text": "text-gray-700"},
    "important": {"bg": "bg-yellow-50", "border": "border-yellow-500", "text": "text-yellow-800"},
    "warning": {"bg": "bg-red-50", "border": "border-red-500", "text": "text-red-800"},
    "other": {"bg": "bg-blue-50", "border": "border-blue-500", "text": "text-blue-700"}
}

def get_icon(content_type: str) -> str:
    return ICON_MAP.get(content_type, "concept")

def get_colors(content_type: str) -> dict:
    return COLOR_MAP.get(content_type, COLOR_MAP["other"])

