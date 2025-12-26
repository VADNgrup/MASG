from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class DesignStyle(Enum):
    PROFESSIONAL_MINIMAL = "professional_minimal"

@dataclass
class ColorPalette:
    name: str
    primary: str
    secondary: str
    accent: str
    background: str
    text_primary: str = "#1a1a1a"
    text_secondary: str = "#6b7280"
    
    def to_dict(self):
        return {
            "name": self.name,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text_primary": self.text_primary,
            "text_secondary": self.text_secondary
        }

@dataclass
class TypographyPair:
    name: str
    heading_font: str
    body_font: str
    scale: float = 1.25 
    base_size: int = 16
    
    def get_sizes(self):
        """Generate type scale"""
        return {
            "xs": round(self.base_size / (self.scale ** 2)),
            "sm": round(self.base_size / self.scale),
            "base": self.base_size,
            "lg": round(self.base_size * self.scale),
            "xl": round(self.base_size * (self.scale ** 2)),
            "2xl": round(self.base_size * (self.scale ** 3)),
            "3xl": round(self.base_size * (self.scale ** 4)),
        }

@dataclass
class LayoutPattern:
    name: str
    type: str 
    proportions: Dict[str, float] 
    whitespace: str 
    alignment: str 

PROFESSIONAL_MINIMAL_PALETTES = [
    ColorPalette(
        name="Classic Blue",
        primary="#2563eb",
        secondary="#93c5fd",
        accent="#0ea5e9",
        background="#ffffff"
    ),
    ColorPalette(
        name="Sophisticated Navy",
        primary="#1e3a8a",
        secondary="#60a5fa",
        accent="#3b82f6",
        background="#f8fafc"
    ),
    ColorPalette(
        name="Modern Slate",
        primary="#334155",
        secondary="#94a3b8",
        accent="#0891b2",
        background="#ffffff"
    ),
    ColorPalette(
        name="Clean Cyan",
        primary="#0891b2",
        secondary="#67e8f9",
        accent="#06b6d4",
        background="#f0fdfa"
    ),
    ColorPalette(
        name="Elegant Indigo",
        primary="#4f46e5",
        secondary="#a5b4fc",
        accent="#6366f1",
        background="#fafafa"
    ),
]

PROFESSIONAL_TYPOGRAPHY_PAIRS = [
    TypographyPair(
        name="Inter System",
        heading_font="Inter",
        body_font="Inter",
        scale=1.25
    ),
    TypographyPair(
        name="Poppins Clean",
        heading_font="Poppins",
        body_font="Inter",
        scale=1.333
    ),
    TypographyPair(
        name="Montserrat Modern",
        heading_font="Montserrat",
        body_font="Open Sans",
        scale=1.25
    ),
    TypographyPair(
        name="DM Sans Minimal",
        heading_font="DM Sans",
        body_font="DM Sans",
        scale=1.2
    ),
    TypographyPair(
        name="Work Sans Professional",
        heading_font="Work Sans",
        body_font="Source Sans Pro",
        scale=1.25
    ),
]

PROFESSIONAL_LAYOUT_PATTERNS = [
    LayoutPattern(
        name="Hero Left",
        type="asymmetric_hero",
        proportions={"image": 0.6, "content": 0.4},
        whitespace="generous",
        alignment="left"
    ),
    LayoutPattern(
        name="Centered Impact",
        type="centered_minimal",
        proportions={"content": 0.8, "margin": 0.2},
        whitespace="generous",
        alignment="center"
    ),
    LayoutPattern(
        name="Split Balance",
        type="split_screen",
        proportions={"left": 0.5, "right": 0.5},
        whitespace="balanced",
        alignment="left"
    ),
    LayoutPattern(
        name="Content Focus",
        type="text_dominant",
        proportions={"content": 0.7, "visual": 0.3},
        whitespace="balanced",
        alignment="left"
    ),
    LayoutPattern(
        name="Visual Hero",
        type="image_hero",
        proportions={"image": 0.7, "text": 0.3},
        whitespace="generous",
        alignment="center"
    ),
]

VISUAL_EFFECTS = {
    "backgrounds": [
        "solid_white",
        "soft_gradient",
        "subtle_texture",
        "dots_pattern",
        "minimal_grid"
    ],
    "shapes": [
        "soft_circle",
        "minimal_square",
        "flowing_blob",
        "geometric_accent"
    ],
    "overlays": [
        "none",
        "subtle_gradient_overlay",
        "glassmorphism"
    ]
}

class DesignTokens:
    @staticmethod
    def get_all_palettes(style: DesignStyle = DesignStyle.PROFESSIONAL_MINIMAL):
        if style == DesignStyle.PROFESSIONAL_MINIMAL:
            return PROFESSIONAL_MINIMAL_PALETTES
        return []
    
    @staticmethod
    def get_all_typography(style: DesignStyle = DesignStyle.PROFESSIONAL_MINIMAL):
        if style == DesignStyle.PROFESSIONAL_MINIMAL:
            return PROFESSIONAL_TYPOGRAPHY_PAIRS
        return []
    
    @staticmethod
    def get_all_layouts(style: DesignStyle = DesignStyle.PROFESSIONAL_MINIMAL):
        if style == DesignStyle.PROFESSIONAL_MINIMAL:
            return PROFESSIONAL_LAYOUT_PATTERNS
        return []
    
    @staticmethod
    def calculate_combinations(style: DesignStyle = DesignStyle.PROFESSIONAL_MINIMAL):
        palettes = len(DesignTokens.get_all_palettes(style))
        typography = len(DesignTokens.get_all_typography(style))
        layouts = len(DesignTokens.get_all_layouts(style))
        
        return palettes * typography * layouts
