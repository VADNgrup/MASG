import json
from src.utils.config import Config
from src.utils.llm import chat
from src.utils.parse_llm_response import parse_json_response


def get_theme(theme_name: str) -> dict:
    with open(Config.THEME_PATH, "r") as f:
        themes = json.load(f)
        for theme in themes:
            if theme["theme"] == theme_name:
                return theme["theme"], theme["font"]
    return "frankfurt", "STIX Two Tex t"


def select_theme(outline_md: str, model = Config.LLM_MODEL_NAME) -> dict:
    with open(Config.THEME_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)

    themes_description = "\n".join(
        f'- "{t["theme"]}": {t.get("serve", "")}' for t in themes
    )
    outline_text = outline_md[:3000]

    prompt = f"""You are a helpful theme selection assistant.

Given the following lecture outline, choose the MOST suitable presentation theme.

## Available Themes
{themes_description}

## Lecture Outline
{outline_text}

## Output
Return ONLY valid JSON with the chosen theme name:
{{"theme": "<theme_name>"}}
"""

    _invoke = lambda msgs: chat(model=model, messages=msgs, temperature=0.2, max_tokens=200)
    response = _invoke([{"role": "user", "content": prompt}])
    result = parse_json_response(response, _invoke, expect_list=False)
    theme_name = result.get("theme", "default") if isinstance(result, dict) else "default"
    return get_theme(theme_name)