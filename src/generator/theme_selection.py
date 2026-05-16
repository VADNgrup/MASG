import json
from src.utils.config import Config
from src.utils.llm import chat
from src.utils.parse_llm_response import parse_json_response

def get_theme(theme_name: str) -> dict:
    with open(Config.THEME_PATH, 'r') as f:
        themes = json.load(f)
        for theme in themes:
            if theme['theme'] == theme_name:
                return (theme['theme'], theme['font'])
    return ('frankfurt', 'STIX Two Tex t')

def select_theme(outline_md: str, model=Config.LLM_MODEL_NAME) -> dict:
    with open(Config.THEME_PATH, 'r', encoding='utf-8') as f:
        themes = json.load(f)
    themes_description = '\n'.join((f'''- "{t['theme']}": {t.get('serve', '')}''' for t in themes))
    outline_text = outline_md[:3000]
    prompt = f'You are a helpful theme selection assistant.\n\nGiven the following lecture outline, choose the MOST suitable presentation theme.\n\n## Available Themes\n{themes_description}\n\n## Lecture Outline\n{outline_text}\n\n## Output\nReturn ONLY valid JSON with the chosen theme name:\n{{"theme": "<theme_name>"}}\n'
    _invoke = lambda msgs: chat(model=model, messages=msgs, temperature=0.2, max_tokens=200)
    try:
        response = _invoke([{'role': 'user', 'content': prompt}])
        result = parse_json_response(response, _invoke, expect_list=False)
        theme_name = result.get('theme', 'default') if isinstance(result, dict) else 'default'
    except Exception as e:
        print(f'[theme_selection] Theme selection failed ({e}); using frankfurt.')
        theme_name = 'frankfurt'
    return get_theme(theme_name)
