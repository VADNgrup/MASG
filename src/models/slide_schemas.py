from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional, Union, Any
from enum import Enum
import re


class SlideType(str, Enum):
    VISUAL = "visual"
    TABLE = "table"
    FORMULA = "formula"
    CARDS = "cards"
    SPLIT_IMAGE_LIST = "split_image_list"
    COMPARISON = "comparison"
    STATS = "stats"
    CODE = "code"
    TIMELINE = "timeline"
    HERO = "hero"
    THANKYOU = "thankyou"


class CardItem(BaseModel):
    heading: str
    description: str
    icon: str = "cube"
    color: str = "blue"


class ListItem(BaseModel):
    heading: str
    description: str


class StatItem(BaseModel):
    value: str
    label: str
    color: str = "blue"


class TimelinePhase(BaseModel):
    title: str
    description: str
    icon: str = "flag"
    status: str = "upcoming"


class ContactItem(BaseModel):
    icon: str
    label: str
    value: str


class BaseSlide(BaseModel):
    slide_type: SlideType
    title: str


class VisualSlide(BaseSlide):
    slide_type: Literal[SlideType.VISUAL] = SlideType.VISUAL
    description: str
    image: Optional[str] = None
    category: Optional[str] = None
    key_points: Optional[List[str]] = None
    caption: Optional[str] = None


class HeroSlide(BaseSlide):
    slide_type: Literal[SlideType.HERO] = SlideType.HERO
    description: str
    image: Optional[str] = None
    category: Optional[str] = None
    stats: Optional[List[StatItem]] = None
    insight_title: Optional[str] = None
    insight_text: Optional[str] = None


class TableSlide(BaseSlide):
    slide_type: Literal[SlideType.TABLE] = SlideType.TABLE
    category: Optional[str] = None
    headers: List[str]
    rows: List[List[str]]


class FormulaSlide(BaseSlide):
    slide_type: Literal[SlideType.FORMULA] = SlideType.FORMULA
    category: Optional[str] = None
    formulas: List[str]
    bullets: Optional[List[str]] = None

    @field_validator('formulas', mode='before')
    @classmethod
    def fix_latex(cls, v: List[str]) -> List[str]:
        fixed = []
        for formula in v:
            for func in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'log', 'ln', 'exp', 'lim', 'sum', 'prod', 'int']:
                formula = re.sub(rf'(?<!\\)\b{func}\b', rf'\\{func}', formula)
            formula = formula.replace('$', '')
            fixed.append(formula)
        return fixed


class CardsSlide(BaseSlide):
    slide_type: Literal[SlideType.CARDS] = SlideType.CARDS
    category: Optional[str] = None
    cards: List[CardItem] = Field(..., min_length=1, max_length=4)


class SplitImageListSlide(BaseSlide):
    slide_type: Literal[SlideType.SPLIT_IMAGE_LIST] = SlideType.SPLIT_IMAGE_LIST
    image: Optional[str] = None
    badge: Optional[str] = None
    items: List[ListItem] = Field(..., min_length=1)


class ComparisonSlide(BaseSlide):
    slide_type: Literal[SlideType.COMPARISON] = SlideType.COMPARISON
    subtitle: Optional[str] = None
    left_title: str = "Cons"
    left_items: List[str]
    right_title: str = "Pros"
    right_items: List[str]


class StatsSlide(BaseSlide):
    slide_type: Literal[SlideType.STATS] = SlideType.STATS
    description: Optional[str] = None
    stats: List[StatItem] = Field(..., min_length=1, max_length=4)
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None


class CodeSlide(BaseSlide):
    slide_type: Literal[SlideType.CODE] = SlideType.CODE
    language: str = "python"
    code: str
    filename: Optional[str] = None


class TimelineSlide(BaseSlide):
    slide_type: Literal[SlideType.TIMELINE] = SlideType.TIMELINE
    subtitle: Optional[str] = None
    phases: List[TimelinePhase]
    tags: Optional[List[str]] = None


class ThankYouSlide(BaseSlide):
    slide_type: Literal[SlideType.THANKYOU] = SlideType.THANKYOU
    subtitle: Optional[str] = None
    contacts: Optional[List[ContactItem]] = None


SlideUnion = Union[
    VisualSlide,
    HeroSlide,
    TableSlide,
    FormulaSlide,
    CardsSlide,
    SplitImageListSlide,
    ComparisonSlide,
    StatsSlide,
    CodeSlide,
    TimelineSlide,
    ThankYouSlide
]

class SlidesDocument(BaseModel):
    slides: List[SlideUnion]

    @classmethod
    def parse_slides(cls, data: dict) -> "SlidesDocument":
        slides = []
        for slide_data in data.get("slides", []):
            slide_type = slide_data.get("slide_type", "visual")
            
            type_map = {
                "visual": VisualSlide,
                "hero": HeroSlide,
                "table": TableSlide,
                "formula": FormulaSlide,
                "cards": CardsSlide,
                "split_image_list": SplitImageListSlide,
                "comparison": ComparisonSlide,
                "stats": StatsSlide,
                "code": CodeSlide,
                "timeline": TimelineSlide,
                "thankyou": ThankYouSlide
            }
            
            model_class = type_map.get(slide_type, VisualSlide)
            try:
                slides.append(model_class(**slide_data))
            except Exception as e:
                slides.append(VisualSlide(
                    title=slide_data.get("title", "Untitled"),
                    description=str(slide_data),
                    slide_type=SlideType.VISUAL
                ))
        
        return cls(slides=slides)


def get_schema_for_prompt() -> str:
    return '''
SLIDE SCHEMAS (JSON format):

1. visual - Simple visual slide
{
  "slide_type": "visual",
  "title": "string",
  "description": "string",
  "image": "string (optional, e.g., img_001_02)",
  "category": "string (optional)"
}

2. hero - Large hero slide with stats
{
  "slide_type": "hero",
  "title": "string",
  "description": "string",
  "image": "string (optional)",
  "category": "string (optional)",
  "stats": [{"value": "85%", "label": "Accuracy", "color": "blue"}],
  "insight_title": "string (optional)",
  "insight_text": "string (optional)"
}

3. table - Data table
{
  "slide_type": "table",
  "title": "string",
  "headers": ["Col1", "Col2", "Col3"],
  "rows": [["a", "b", "c"], ["d", "e", "f"]]
}

4. formula - Mathematical formulas (LaTeX WITHOUT $ delimiters)
{
  "slide_type": "formula",
  "title": "string",
  "formulas": ["\\\\sin^2 x + \\\\cos^2 x = 1", "E = mc^2"],
  "bullets": ["Introduction point (optional)"]
}

5. cards - Three-column feature cards
{
  "slide_type": "cards",
  "title": "string",
  "category": "string (optional)",
  "cards": [
    {"heading": "Feature 1", "description": "Details", "icon": "cube", "color": "blue"},
    {"heading": "Feature 2", "description": "Details", "icon": "chart-line", "color": "purple"},
    {"heading": "Feature 3", "description": "Details", "icon": "rocket", "color": "green"}
  ]
}

6. split_image_list - Image + numbered list
{
  "slide_type": "split_image_list",
  "title": "string",
  "image": "string (optional)",
  "badge": "string (optional)",
  "items": [
    {"heading": "Step 1", "description": "Details"},
    {"heading": "Step 2", "description": "Details"}
  ]
}

7. comparison - Pros/cons comparison
{
  "slide_type": "comparison",
  "title": "string",
  "subtitle": "string (optional)",
  "left_title": "Disadvantages",
  "left_items": ["Con 1", "Con 2"],
  "right_title": "Advantages",
  "right_items": ["Pro 1", "Pro 2"]
}

8. stats - Metrics showcase
{
  "slide_type": "stats",
  "title": "string",
  "description": "string (optional)",
  "stats": [
    {"value": "99%", "label": "Uptime", "color": "green"},
    {"value": "50K+", "label": "Users", "color": "blue"}
  ]
}

9. code - Code display
{
  "slide_type": "code",
  "title": "string",
  "language": "python",
  "code": "def hello():\\n    print('Hello')",
  "filename": "example.py (optional)"
}

10. timeline - Roadmap/timeline
{
  "slide_type": "timeline",
  "title": "string",
  "subtitle": "string (optional)",
  "phases": [
    {"title": "Phase 1", "description": "Details", "icon": "flag", "status": "completed"},
    {"title": "Phase 2", "description": "Details", "icon": "rocket", "status": "current"}
  ],
  "tags": ["Q1 2024", "Launch"]
}

11. thankyou - Closing slide
{
  "slide_type": "thankyou",
  "title": "Thank You",
  "subtitle": "string (optional)",
  "contacts": [
    {"icon": "email", "label": "Email", "value": "example@email.com"}
  ]
}
'''
