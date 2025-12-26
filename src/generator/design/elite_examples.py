from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class DesignElement(Enum):
    LAYOUT = "layout"
    TYPOGRAPHY = "typography"
    COLOR = "color"
    SPACING = "spacing"
    VISUAL_HIERARCHY = "visual_hierarchy"
    IMAGERY = "imagery"

@dataclass
class EliteExample:
    """Represents one elite design example with detailed analysis"""
    
    id: str
    name: str
    style: str
    screenshot_path: str
    
    layout_type: str
    layout_proportions: Dict[str, float]
    grid_system: str
    
    heading_font: str
    body_font: str
    heading_size: int
    body_size: int
    line_height: float
    letter_spacing: str
    
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    color_scheme: str
    
    whitespace_approach: str
    padding_scale: str
    margin_system: str
    
    focal_point: str
    reading_pattern: str
    contrast_ratio: float
    
    special_effects: List[str]
    animations: List[str]
    
    why_elite: str
    key_learnings: List[str]
    
    def to_llm_prompt(self) -> str:
        """Convert to LLM-friendly description"""
        return f"""
ELITE EXAMPLE: {self.name}

Layout:
- Type: {self.layout_type}
- Proportions: {self.layout_proportions}
- Grid: {self.grid_system}

Typography:
- Heading: {self.heading_font} at {self.heading_size}px
- Body: {self.body_font} at {self.body_size}px
- Line height: {self.line_height}
- Letter spacing: {self.letter_spacing}

Colors:
- Scheme: {self.color_scheme}
- Primary: {self.primary_color}
- Secondary: {self.secondary_color}
- Accent: {self.accent_color}
- Background: {self.background_color}

Spacing:
- Whitespace: {self.whitespace_approach}
- Padding: {self.padding_scale}
- Margins: {self.margin_system}

Visual Hierarchy:
- Focal point: {self.focal_point}
- Reading pattern: {self.reading_pattern}
- Contrast ratio: {self.contrast_ratio}

Special Techniques:
- Effects: {', '.join(self.special_effects)}
- Animations: {', '.join(self.animations)}

Why Elite: {self.why_elite}

Key Learnings:
{chr(10).join(f"- {learning}" for learning in self.key_learnings)}
"""

PROFESSIONAL_MINIMAL_EXAMPLES = [
    EliteExample(
        id="pm_001",
        name="Clean Tech Hero",
        style="professional_minimal",
        screenshot_path="data/design/examples/pm_001.png",
        
        layout_type="asymmetric_hero",
        layout_proportions={"content": 0.45, "image": 0.55},
        grid_system="12-column",
        
        heading_font="Inter",
        body_font="Inter",
        heading_size=64,
        body_size=18,
        line_height=1.6,
        letter_spacing="normal",
        
        primary_color="#2563eb",
        secondary_color="#93c5fd",
        accent_color="#0ea5e9",
        background_color="#ffffff",
        color_scheme="monochromatic",
        
        whitespace_approach="generous",
        padding_scale="16px base",
        margin_system="multiples of 16",
        
        focal_point="center-left",
        reading_pattern="F-pattern",
        contrast_ratio=7.5,
        
        special_effects=["gradient_text", "subtle_shadow", "rounded_corners"],
        animations=["fade_in"],
        
        why_elite="Perfect balance of content and visuals, excellent use of whitespace, professional yet modern",
        key_learnings=[
            "Use 45/55 split for content/image balance",
            "Generous whitespace creates premium feel",
            "Gradient text adds visual interest without overwhelming"
        ]
    ),
    
    EliteExample(
        id="pm_002",
        name="Centered Statement",
        style="professional_minimal",
        screenshot_path="data/design/examples/pm_002.png",
        
        layout_type="centered_minimal",
        layout_proportions={"content": 0.6, "margin": 0.4},
        grid_system="centered",
        
        heading_font="Poppins",
        body_font="Inter",
        heading_size=72,
        body_size=20,
        line_height=1.5,
        letter_spacing="tight",
        
        primary_color="#1e3a8a",
        secondary_color="#60a5fa",
        accent_color="#3b82f6",
        background_color="#f8fafc",
        color_scheme="monochromatic",
        
        whitespace_approach="generous",
        padding_scale="24px base",
        margin_system="golden ratio",
        
        focal_point="center",
        reading_pattern="centered",
        contrast_ratio=8.0,
        
        special_effects=["large_typography", "minimal_decoration"],
        animations=[],
        
        why_elite="Impact through simplicity, perfect for key messages, excellent typography hierarchy",
        key_learnings=[
            "Center alignment for maximum impact",
            "Large heading size (72px) demands attention",
            "Subtle background color adds warmth without distraction"
        ]
    ),
    
]

class EliteExamplesLibrary:
    """Manages the library of elite design examples"""
    
    @staticmethod
    def get_examples(style: str = "professional_minimal") -> List[EliteExample]:
        """Get all examples for a style"""
        if style == "professional_minimal":
            return PROFESSIONAL_MINIMAL_EXAMPLES
        return []
    
    @staticmethod
    def get_examples_for_llm(style: str = "professional_minimal") -> str:
        """Get formatted examples for LLM prompt"""
        examples = EliteExamplesLibrary.get_examples(style)
        return "\n\n---\n\n".join([ex.to_llm_prompt() for ex in examples])
    
    @staticmethod
    def analyze_patterns(style: str = "professional_minimal") -> Dict[str, Any]:
        """Analyze common patterns across examples"""
        examples = EliteExamplesLibrary.get_examples(style)
        
        # Extract common patterns
        layout_types = [ex.layout_type for ex in examples]
        color_schemes = [ex.color_scheme for ex in examples]
        whitespace = [ex.whitespace_approach for ex in examples]
        
        return {
            "common_layouts": list(set(layout_types)),
            "common_color_schemes": list(set(color_schemes)),
            "common_whitespace": list(set(whitespace)),
            "total_examples": len(examples)
        }
