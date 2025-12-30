from langchain_openai import ChatOpenAI
from typing import Dict, Any, Optional
import subprocess
import time
from pathlib import Path
from src.utils.config import config

class SlidevValidatorAgent:
    def __init__(self, model: str = "gpt-4o", slidev_dir: str = "slidev"):
        self.llm = ChatOpenAI(model=model, temperature=0.1, max_tokens=8000)
        self.model = model
        self.slidev_dir = Path(slidev_dir)
        self.max_retries = 3
    
    def check_terminal_errors(self, timeout: int = 10) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(self.slidev_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=timeout,
                shell=True
            )
            
            has_errors = result.returncode != 0
            error_output = result.stderr if has_errors else ""
            
            return {
                "has_errors": has_errors,
                "error_output": error_output,
                "stdout": result.stdout,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "has_errors": True,
                "error_output": "Build timeout exceeded",
                "stdout": "",
                "return_code": -1
            }
        except Exception as e:
            return {
                "has_errors": True,
                "error_output": str(e),
                "stdout": "",
                "return_code": -1
            }
    
    def analyze_and_fix_errors(self, markdown_content: str, error_info: Dict[str, Any]) -> str:
        system_prompt = """You are a Slidev debugging expert who fixes markdown errors.

COMMON ERRORS TO FIX:

1. LATEX SYNTAX ERRORS:
   - Missing closing braces: $\\frac{a}{b$ → $\\frac{a}{b}$
   - Wrong escaping: $\\alpha$ might need $$\\alpha$$
   - Special characters: Use proper LaTeX commands

2. HTML/VUE ERRORS:
   - Unclosed tags: <div> without </div>
   - Invalid attributes
   - Wrong class names

3. MARKDOWN ERRORS:
   - Malformed tables
   - Missing frontmatter
   - Invalid YAML

4. COMPONENT ERRORS:
   - Unknown carbon icons
   - Invalid v-motion directives

FIXING STRATEGY:
- Read error message carefully
- Identify the problematic line/section
- Apply minimal fix
- Preserve all content and styling
- Don't change working parts

Return ONLY the fixed markdown, no explanations."""

        user_prompt = f"""Fix this Slidev markdown that has errors:

ERROR INFO:
{error_info['error_output']}

CURRENT MARKDOWN:
{markdown_content}

Fix the errors and return the corrected markdown:"""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        fixed_content = response.content.strip()
        
        if "```markdown" in fixed_content:
            fixed_content = fixed_content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in fixed_content:
            fixed_content = fixed_content.split("```")[1].split("```")[0].strip()
        
        return fixed_content
    
    def validate_and_fix(self, markdown_content: str, slides_path: str = "slidev/slides.md") -> Dict[str, Any]:
        slides_file = Path(slides_path)
        slides_file.write_text(markdown_content, encoding='utf-8')
        
        for attempt in range(self.max_retries):
            print(f"Validation attempt {attempt + 1}/{self.max_retries}...")
            
            time.sleep(2)
            
            error_info = self.check_terminal_errors()
            
            if not error_info["has_errors"]:
                print("✓ Slidev build successful!")
                return {
                    "success": True,
                    "markdown": markdown_content,
                    "attempts": attempt + 1,
                    "errors": None
                }
            
            print(f"✗ Build errors detected:")
            print(error_info["error_output"][:500])
            
            if attempt < self.max_retries - 1:
                print(f"Attempting to fix errors...")
                markdown_content = self.analyze_and_fix_errors(markdown_content, error_info)
                slides_file.write_text(markdown_content, encoding='utf-8')
            else:
                print(f"Max retries reached. Returning last version with errors.")
                return {
                    "success": False,
                    "markdown": markdown_content,
                    "attempts": attempt + 1,
                    "errors": error_info
                }
        
        return {
            "success": False,
            "markdown": markdown_content,
            "attempts": self.max_retries,
            "errors": error_info
        }
