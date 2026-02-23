import pinkyne_extension
from langchain_openai import ChatOpenAI
from typing import Dict, Any, Optional, List
import subprocess
import time
import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    LATEX = "latex"
    HTML = "html"
    YAML = "yaml"
    VUE = "vue"
    UNKNOWN = "unknown"


@dataclass
class ParsedError:
    error_type: ErrorType
    message: str
    line_number: Optional[int]
    context: Optional[str]


class ErrorAnalyzer:
    LATEX_PATTERNS = [
        r"KaTeX.*error",
        r"Unexpected.*math",
        r"Invalid.*formula",
        r"\$.*not.*closed",
        r"MathJax",
    ]
    
    HTML_PATTERNS = [
        r"Unclosed.*tag",
        r"Invalid.*attribute",
        r"Unexpected.*token.*<",
        r"Expected.*>",
    ]
    
    VUE_PATTERNS = [
        r"v-motion",
        r"carbon:",
        r"component.*not.*found",
        r"Unknown.*directive",
    ]
    
    YAML_PATTERNS = [
        r"YAML.*error",
        r"frontmatter",
        r"Invalid.*layout",
    ]
    
    def analyze(self, error_output: str) -> List[ParsedError]:
        errors = []
        
        for pattern in self.LATEX_PATTERNS:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(ParsedError(
                    error_type=ErrorType.LATEX,
                    message=self._extract_message(error_output, pattern),
                    line_number=self._extract_line_number(error_output),
                    context=self._extract_context(error_output)
                ))
        
        for pattern in self.HTML_PATTERNS:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(ParsedError(
                    error_type=ErrorType.HTML,
                    message=self._extract_message(error_output, pattern),
                    line_number=self._extract_line_number(error_output),
                    context=self._extract_context(error_output)
                ))
        
        for pattern in self.VUE_PATTERNS:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(ParsedError(
                    error_type=ErrorType.VUE,
                    message=self._extract_message(error_output, pattern),
                    line_number=self._extract_line_number(error_output),
                    context=self._extract_context(error_output)
                ))
        
        for pattern in self.YAML_PATTERNS:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(ParsedError(
                    error_type=ErrorType.YAML,
                    message=self._extract_message(error_output, pattern),
                    line_number=self._extract_line_number(error_output),
                    context=self._extract_context(error_output)
                ))
        
        if not errors:
            errors.append(ParsedError(
                error_type=ErrorType.UNKNOWN,
                message=error_output[:500],
                line_number=None,
                context=None
            ))
        
        return errors
    
    def _extract_message(self, output: str, pattern: str) -> str:
        match = re.search(f".*{pattern}.*", output, re.IGNORECASE)
        return match.group(0) if match else output[:200]
    
    def _extract_line_number(self, output: str) -> Optional[int]:
        match = re.search(r"line[:\s]+(\d+)", output, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r":(\d+):", output)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_context(self, output: str) -> Optional[str]:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'error' in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                return '\n'.join(lines[start:end])
        return None


class SlidevValidatorAgent:
    def __init__(self, model: str = "gpt-4o", slidev_dir: str = "slidev"):
        self.llm = ChatOpenAI(model=model, temperature=0.1)
        self.model = model
        self.slidev_dir = Path(slidev_dir)
        self.max_retries = 3
        self.error_analyzer = ErrorAnalyzer()
        self.error_history: List[Dict[str, Any]] = []
    
    def check_terminal_errors(self, timeout: int = 30) -> Dict[str, Any]:
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
            
            if has_errors and not error_output:
                error_output = result.stdout
            
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
    
    def _build_fix_prompt(self, markdown_content: str, error_info: Dict[str, Any], attempt: int) -> tuple:
        parsed_errors = self.error_analyzer.analyze(error_info['error_output'])
        
        error_summary = "\n".join([
            f"- Type: {e.error_type.value}, Line: {e.line_number or 'unknown'}, Message: {e.message[:200]}"
            for e in parsed_errors
        ])
        
        history_context = ""
        if self.error_history:
            history_context = "\n\nPREVIOUS FIX ATTEMPTS:\n"
            for h in self.error_history[-2:]:
                history_context += f"- Attempt {h['attempt']}: {h['error_type']} - {h['fix_applied'][:100]}\n"
        
        system_prompt = f"""You are a Slidev markdown debugger. Fix the errors based on analysis.

ERROR ANALYSIS:
{error_summary}
{history_context}

FIX STRATEGIES BY ERROR TYPE:

LATEX ERRORS:
- Ensure all math is wrapped in $$ for block or $ for inline
- Use proper LaTeX: \\sin, \\cos, \\frac{{{{}}}}{{{{}}}}, \\sqrt{{{{}}}}
- Close all braces properly
- Escape special chars in LaTeX

HTML/VUE ERRORS:
- Close all tags properly
- Remove invalid attributes
- Check v-motion directives syntax

YAML ERRORS:
- Ensure --- delimiters are correct
- Check layout names are valid
- Proper indentation

ATTEMPT {attempt}/{self.max_retries} - Be more aggressive if previous fixes didn't work.

Return ONLY the fixed markdown, no explanations."""

        user_prompt = f"""Fix this Slidev markdown:

RAW ERROR:
{error_info['error_output'][:1000]}

MARKDOWN:
{markdown_content}

Return the corrected markdown:"""

        return system_prompt, user_prompt
    
    def analyze_and_fix_errors(self, markdown_content: str, error_info: Dict[str, Any], attempt: int) -> str:
        system_prompt, user_prompt = self._build_fix_prompt(markdown_content, error_info, attempt)
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        fixed_content = response.content.strip()
        
        if "```markdown" in fixed_content:
            fixed_content = fixed_content.split("```markdown")[1].split("```")[0].strip()
        elif "```md" in fixed_content:
            fixed_content = fixed_content.split("```md")[1].split("```")[0].strip()
        elif "```" in fixed_content:
            parts = fixed_content.split("```")
            if len(parts) >= 3:
                fixed_content = parts[1].strip()
        
        parsed_errors = self.error_analyzer.analyze(error_info['error_output'])
        self.error_history.append({
            "attempt": attempt,
            "error_type": parsed_errors[0].error_type.value if parsed_errors else "unknown",
            "fix_applied": fixed_content[:100]
        })
        
        return fixed_content
    
    def validate_and_fix(self, markdown_content: str, slides_path: str = "slidev/slides.md") -> Dict[str, Any]:
        slides_file = Path(slides_path)
        slides_file.write_text(markdown_content, encoding='utf-8')
        
        self.error_history.clear()
        
        for attempt in range(1, self.max_retries + 1):
            print(f"Validation attempt {attempt}/{self.max_retries}...")
            
            time.sleep(2)
            
            error_info = self.check_terminal_errors()
            
            if not error_info["has_errors"]:
                print("✓ Slidev build successful!")
                return {
                    "success": True,
                    "markdown": markdown_content,
                    "attempts": attempt,
                    "errors": None
                }
            
            parsed_errors = self.error_analyzer.analyze(error_info["error_output"])
            print(f"✗ Build errors detected:")
            for err in parsed_errors[:3]:
                print(f"  - [{err.error_type.value}] {err.message[:100]}")
            
            if attempt < self.max_retries:
                print(f"Attempting fix #{attempt}...")
                markdown_content = self.analyze_and_fix_errors(markdown_content, error_info, attempt)
                slides_file.write_text(markdown_content, encoding='utf-8')
            else:
                print(f"Max retries reached. Returning last version.")
                return {
                    "success": False,
                    "markdown": markdown_content,
                    "attempts": attempt,
                    "errors": error_info,
                    "parsed_errors": [{"type": e.error_type.value, "message": e.message} for e in parsed_errors]
                }
        
        return {
            "success": False,
            "markdown": markdown_content,
            "attempts": self.max_retries,
            "errors": error_info
        }
