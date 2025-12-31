from langchain_openai import ChatOpenAI
from pathlib import Path
from typing import Dict, Any, List
import json
import re

class TemplateMatcher:
    def __init__(self, template_name: str = "dark_modern", model: str = "gpt-4o-mini"):
        self.template_name = template_name
        self.llm = ChatOpenAI(model=model, temperature=0.1)
        self.template_dir = Path(f"data/templates/{template_name}")
        
        self.components = self._discover_components()
        
        self.component_context = self._build_component_context()
    
    def _discover_components(self) -> Dict[str, Dict]:
        components = {}
        
        for component_file in self.template_dir.glob("*.md"):
            if component_file.stem == "config":
                continue
            
            content = component_file.read_text(encoding='utf-8')
            
            variables = re.findall(r'\{\{\s*(\w+)', content)
            
            frontmatter = self._extract_frontmatter(content)
            
            components[component_file.stem] = {
                "file": component_file.name,
                "variables": list(set(variables)),
                "layout": frontmatter.get("layout", "default"),
                "description": self._infer_component_purpose(component_file.stem)
            }
        
        return components
    
    def _extract_frontmatter(self, content: str) -> Dict[str, str]:
        if not content.startswith("---"):
            return {}
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        
        frontmatter = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def _infer_component_purpose(self, name: str) -> str:
        purposes = {
            "hero": "Large hero slide with title, description, image, optional stats and insight box. Best for opening slides or major section breaks.",
            "visual": "Simple visual slide with title, description and image. Cleaner than hero, no stats.",
            "table": "Tabular data display with headers and rows for structured information.",
            "formula": "Mathematical formulas with LaTeX rendering, includes optional bullet points.",
            "cards": "Three-column card layout with icons, perfect for 3-step processes or feature lists.",
            "split_image_list": "Two-column layout: image on left, numbered list on right. Good for step-by-step explanations.",
            "stats": "Metrics showcase with 2x2 grid of statistics, includes optional CTA button.",
            "comparison": "Side-by-side comparison with pros/cons or before/after scenarios.",
            "code": "Code display with terminal-style window and syntax highlighting.",
            "timeline": "Roadmap or timeline with milestones, icons, phases, and tags.",
            "thankyou": "Closing slide with large title, gradient text, and contact information grid."
        }
        return purposes.get(name, f"General {name} slide component")
    
    def _build_component_context(self) -> str:
        """Build context string describing all available components."""
        lines = ["Available slide components:\n"]
        
        for name, info in sorted(self.components.items()):
            lines.append(f"• **{name}**: {info['description']}")
            lines.append(f"  Required fields: {', '.join(info['variables'][:5])}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def match_component(self, slide: Dict[str, Any]) -> str:
        """Use LLM to select the best component for the slide."""
        
        system_prompt = f"""You are a presentation design expert selecting the best slide component.

{self.component_context}

TASK: Analyze the slide content structure and choose the MOST APPROPRIATE component.

RULES:
1. Match content type to component capabilities
2. Consider if slide has: images, tables, formulas, lists, code, metrics
3. Prefer simpler components when suitable  
4. Ensure all required fields can be populated from slide data

OUTPUT: Return ONLY the component name (e.g., "hero", "cards", "table")
"""

        user_prompt = f"""Select component for this slide:

```json
{json.dumps(slide, ensure_ascii=False, indent=2)}
```

Which component is the best match?"""

        try:
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            component = response.content.strip().lower()
            component = component.replace(".md", "").replace("```", "").replace('"', '').strip()
            
            if component not in self.components:
                print(f"LLM selected unknown component '{component}', falling back to 'visual'")
                return "visual"
            
            print(f"✓ Selected component: {component}")
            return component
            
        except Exception as e:
            print(f"Error in LLM matching: {e}, falling back to 'visual'")
            return "visual"
    
    def match_all(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match components for all slides and return enriched slide data."""
        enriched_slides = []
        
        for idx, slide in enumerate(slides):
            print(f"\n[{idx+1}/{len(slides)}] Processing slide: {slide.get('title', 'Untitled')[:40]}...")
            
            component = self.match_component(slide)
            
            enriched_slide = slide.copy()
            enriched_slide["_component"] = component
            enriched_slide["_component_file"] = f"{component}.md"
            
            enriched_slides.append(enriched_slide)
        
        return enriched_slides
