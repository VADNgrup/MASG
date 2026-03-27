import json
import llm_extension
from langchain_openai import ChatOpenAI
from src.utils.config import Config
from src.utils.parse_llm_response import parse_json_response


def get_theme(theme_name: str) -> dict:
    with open(Config.THEME_PATH, "r") as f:
        themes = json.load(f)
        for theme in themes:
            if theme["theme"] == theme_name:
                return theme["theme"], theme["font"]
    return "frankfurt", "STIX Two Tex t"


def select_theme(lecture , model = Config.LLM_MODEL_NAME) -> dict:
    with open(Config.THEME_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)

    themes_description = "\n".join(
        f'- "{t["theme"]}": {t.get("serve", "")}' for t in themes
    )
    lecture = json.dumps(lecture)[:5000]

    prompt = f"""You are a helpful theme selection assistant.

Given the following lecture/document content, choose the MOST suitable presentation theme.

## Available Themes
{themes_description}

## Content
{lecture}

## Output
Return ONLY valid JSON with the chosen theme name:
{{"theme": "<theme_name>"}}
"""

    llm = ChatOpenAI(model=model, temperature=0.2, max_tokens=200)
    response = llm.invoke([{"role": "user", "content": prompt}])
    result = parse_json_response(response.content, llm.invoke, expect_list=False)

    theme_name = result.get("theme", "default") if isinstance(result, dict) else "default"
    return get_theme(theme_name)