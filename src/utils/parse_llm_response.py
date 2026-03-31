import json
import re
from typing import Any, Callable, Dict, List, Union


def clear_think(content: str) -> str:
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

def extract_json_block(content: str) -> str:
    content = content.strip()
    content = clear_think(content)

    if "```json" in content:
        parts = content.split("```json")
        if len(parts) > 1:
            content = parts[1].split("```")[0]
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            content = parts[1]
    return content.strip()


def parse_json_response(
    response_content: str,
    llm_invoke_fn: Callable,
    retry_count: int = 0,
    expect_list: bool = True,
) -> Union[List[Dict], Dict]:
    """
    Parse JSON from LLM response string.

    Args:
        response_content: Raw string content from LLM.
        llm_invoke_fn: A callable(messages: list) -> object-with-.content OR str.
                       Used for retry/fix when JSON is broken.
        retry_count: Internal retry counter.
        expect_list: If True, always return a list; if False, return dict.
    """
    content = extract_json_block(response_content)
    try:
        result = json.loads(content)
        if expect_list:
            if isinstance(result, list):
                return result
            return [result]
        return result
    except json.JSONDecodeError as e:
        if retry_count >= 2:
            if expect_list:
                return []
            raise ValueError(f"Failed to parse JSON after {retry_count} retries: {str(e)[:200]}") from e

        fixed_content = llm_fix_json(content, str(e), llm_invoke_fn)
        return parse_json_response(fixed_content, llm_invoke_fn, retry_count + 1, expect_list)


def llm_fix_json(broken_json: str, error_message: str, llm_invoke_fn: Callable) -> str:
    fix_prompt = f"""The following JSON has a syntax error. Fix it and return ONLY the corrected JSON.

ERROR: {error_message}

BROKEN JSON:
{broken_json[:3000]}

COMMON ISSUES TO FIX:
1. Escape backslashes in LaTeX: \\frac, \\sin should be \\\\frac, \\\\sin in JSON strings
2. Escape special characters: newlines should be \\n
3. Close unclosed strings, braces, brackets
4. Remove trailing commas before closing braces/brackets

Return ONLY the fixed valid JSON, no explanations:"""

    response = llm_invoke_fn([{"role": "user", "content": fix_prompt}])

    # Support both: raw-string return and object-with-.content return
    if isinstance(response, str):
        return response.strip()
    return response.content.strip()
