from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
from pathlib import Path
from src.utils.config import config

class MarkdownAgent:
    def __init__(self, model: str = "gpt-4o", template_path: str = "data/template/1.md"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        self.model = model
        self.template_path = template_path
        self.template_content = self._load_template()
    
    def _load_template(self) -> str:
        template_file = Path(self.template_path)
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        return ""
    
    def generate_slidev_markdown(self, lecture_data: Dict[str, Any]) -> str:
        system_prompt = f"""You are a Slidev markdown expert who generates beautiful presentation slides.

TEMPLATE LEARNING:
Study this template carefully to understand the Slidev markdown structure:

{self.template_content}

KEY PATTERNS TO FOLLOW:

1. FRONTMATTER STRUCTURE:
   - Each slide starts with ---
   - layout: Standard (or other layouts)
   - class: styling classes
   - transition: slide-left
   - End with ---

2. HTML + TAILWIND STYLING:
   - Use <div class="grid grid-cols-12 h-full w-full"> for layout
   - Modern dark theme: bg-[#0a0a0a], text-gray-100
   - Gradients: bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400
   - Rounded corners: rounded-[2rem], rounded-xl
   - Backdrop blur: backdrop-blur-xl
   - Borders: border border-white/10
   - Shadows: shadow-xl shadow-purple-900/10

3. LATEX FORMULAS - CRITICAL STANDALONE RULE:
   - CRITICAL: LaTeX MUST be completely outside ALL div/HTML structures
   - LaTeX cannot be a child of ANY HTML element
   
   WRONG - LaTeX inside parent div:
   ```
   <div class="grid grid-cols-12">
     <div class="col-span-12">
       <p>Text here</p>
       $$formula$$
     </div>
   </div>
   ```
   
   CORRECT - LaTeX outside all divs:
   ```
   <div class="grid grid-cols-12">
     <div class="col-span-12">
       <p>Text here</p>
     </div>
   </div>
   
   $$formula$$
   ```
   
   CORRECT - Multiple formulas:
   ```
   <div class="col-span-6">
     <p class="mb-4">Formula 1:</p>
   </div>
   
   $$\\\\sin^2 x + \\\\cos^2 x = 1$$
   
   <div class="col-span-6">
     <p class="mb-4">Formula 2:</p>
   </div>
   
   KEY RULES:
   - Close ALL divs before writing LaTeX
   - LaTeX must be at root level of slide (after frontmatter ---)
   - Use single backslash in LaTeX: \\sin not \\\\sin
   - For inline math in text: use $...$
   - For display math: use $$...$$ on separate lines


4. ICONS:
   - Use carbon icons: <carbon:icon-name class="text-2xl text-blue-400" />
   - Examples: carbon:chart-line-data, carbon:idea, carbon:data-base

5. ANIMATIONS:
   - v-motion-slide-top, v-motion-slide-left, v-motion-slide-right
   - v-motion-pop for pop effects
   - :delay="100" for staggered animations

6. TABLES:
   - If table_content exists, render as markdown table
   - Style with Tailwind classes
   - Keep table structure clean

7. LAYOUT PATTERNS:
   - Hero slides: col-span-5 for text, col-span-7 for image
   - Content slides: col-span-6 split or col-span-12 full
   - Cards: p-8 bg-white/5 border border-white/10 rounded-[2rem]

GENERATION RULES:
- Generate ONE complete Slidev markdown file
- Each slide separated by ---
- Use design-ready JSON input (title, intent, layout_hint, density, components)
- Match layout_hint to appropriate template pattern
- Preserve ALL LaTeX formulas as standalone (not wrapped)
- Preserve ALL table markdown
- Use Vietnamese for content
- Modern, professional styling
- Smooth transitions

Return ONLY the complete Slidev markdown, no explanations."""

        user_prompt = f"""Generate a complete Slidev presentation from this lecture data:

{json.dumps(lecture_data, ensure_ascii=False, indent=2)}

Requirements:
1. Create beautiful slides following the template style
2. Use appropriate layouts based on intent and layout_hint
3. LaTeX formulas MUST be standalone (not wrapped in tags)
4. Tables rendered as markdown tables
5. Modern dark theme with gradients
6. Smooth animations
7. Professional typography

Generate the complete markdown now:"""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        markdown_content = response.content.strip()
        
        if "```markdown" in markdown_content:
            markdown_content = markdown_content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in markdown_content:
            markdown_content = markdown_content.split("```")[1].split("```")[0].strip()
        
        markdown_content = self._fix_latex_escaping(markdown_content)
        
        return markdown_content
    
    def _fix_latex_escaping(self, content: str) -> str:
        import re
        
        def fix_formula(match):
            formula = match.group(0)
            formula = formula.replace('\\\\', '\\')
            return formula
        
        content = re.sub(r'\$\$[^$]+\$\$', fix_formula, content, flags=re.DOTALL)
        content = re.sub(r'\$[^$]+\$', fix_formula, content)
        
        return content
    
    def save_to_slidev(self, markdown_content: str, output_path: str = "slidev/slides.md") -> str:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_content, encoding='utf-8')
        return str(output_file)
