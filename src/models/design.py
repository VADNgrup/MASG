from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class ColorPalette(BaseModel):
    """Color scheme for slides"""
    primary: str = Field(description="Primary brand color (hex)")
    secondary: str = Field(description="Secondary accent color (hex)")
    accent: str = Field(description="Accent/highlight color (hex)")
    background: str = Field(description="Background color (hex)")
    text: str = Field(description="Primary text color (hex)")
    text_secondary: str = Field(description="Secondary text color (hex)")
    success: str = "#10b981"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    
    def to_gradient(self, direction: str = "to-br") -> str:
        """Generate Tailwind gradient class"""
        return f"bg-gradient-{direction} from-{self.primary} via-{self.secondary} to-{self.accent}"

class TypographyConfig(BaseModel):
    """Typography settings"""
    heading_font: str = "font-black"
    body_font: str = "font-normal"
    code_font: str = "font-mono"
    heading_size: str = "text-5xl"
    body_size: str = "text-lg"
    line_height: str = "leading-relaxed"

class LayoutConfig(BaseModel):
    """Layout configuration for a slide"""
    layout_type: Literal[
        "standard",           # Regular content layout
        "split-view",         # Text + image side-by-side
        "visual-heavy",       # Large image with minimal text
        "text-focused",       # Text-only, no images
        "grid",               # Grid layout for multiple items
        "hero",               # Hero/title slide
        "comparison",         # Side-by-side comparison
        "timeline",           # Timeline/sequential
        "data-viz"            # Data visualization focused
    ]
    columns: int = 1
    image_position: Optional[Literal["left", "right", "top", "bottom", "background"]] = None
    text_alignment: Literal["left", "center", "right"] = "left"
    padding: str = "p-16"
    gap: str = "gap-8"

class AnimationConfig(BaseModel):
    """Animation settings"""
    entrance: Optional[str] = None  # e.g., "fade-in", "slide-up"
    transition: Optional[str] = None  # e.g., "slide-left", "fade"
    duration: str = "duration-300"
    easing: str = "ease-in-out"

class DesignTokens(BaseModel):
    """Complete design tokens for a slide"""
    slide_id: str
    colors: ColorPalette
    typography: TypographyConfig
    layout: LayoutConfig
    animations: AnimationConfig
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_tailwind_classes(self) -> str:
        """Generate Tailwind CSS classes string"""
        classes = [
            self.colors.to_gradient(),
            self.typography.heading_font,
            self.layout.padding,
            self.layout.gap,
            self.animations.duration,
            self.animations.easing
        ]
        return " ".join(filter(None, classes))

class DesignRecommendation(BaseModel):
    """Design recommendation from Visual Design Agent"""
    slide_id: str
    design_tokens: DesignTokens
    reasoning: str = Field(description="Why these design choices were made")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in design choices")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)

class VisualDesignFeedback(BaseModel):
    """Feedback on visual design quality"""
    overall_score: float
    color_harmony: float
    layout_balance: float
    typography_quality: float
    visual_hierarchy: float
    accessibility_score: float
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
