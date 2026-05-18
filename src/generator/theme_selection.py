import json
from src.utils.config import Config

import re

def get_theme(theme_name: str) -> dict:
    with open(Config.THEME_PATH, 'r') as f:
        themes = json.load(f)
        for theme in themes:
            if theme['theme'] == theme_name:
                return (theme['theme'], theme['font'])
    return ('seriph', 'Roboto')

def select_theme(outline_md: str, model=Config.LLM_MODEL_NAME) -> dict:
    from src.utils.llm import chat
    
    with open(Config.THEME_PATH, 'r', encoding='utf-8') as f:
        themes = json.load(f)
        
    themes_desc = []
    for t in themes:
        themes_desc.append(f"- Name: {t['theme']}\n  Description: {t['serve']}")
    themes_str = "\n".join(themes_desc)
    
    prompt = f"""You are a presentation design expert. Your task is to select the single best presentation theme from the list of available themes based on the provided lecture outline.

Available Themes:
{themes_str}

Lecture Outline:
\"\"\"
{outline_md}
\"\"\"

Critique:
- 'scholarly' has a light cream/beige background which might look too plain or clash with high-contrast elements. Only select it if the content is highly formal academic writing, technical standards, or scientific reports where dense text readability is absolute.
- 'frankfurt' features a highly structured sidebar navigation and dark professional footer bar, which is excellent for formal university lectures and academic courses.
- 'seriph' is a clean minimalist general-purpose theme.
- 'improving-25' is modern tech startup style.
- 'umn' is energetic and academic.

Respond with ONLY the name of the selected theme as a single word in lowercase (e.g. 'frankfurt', 'scholarly', etc.). Do not include any explanation or other text."""

    try:
        messages = [{"role": "user", "content": prompt}]
        selected = chat(model=model, messages=messages, temperature=0.1).strip().lower()
        # Clean selected string in case the LLM returned markdown or quotes
        selected = re.sub(r"[^a-z0-9_-]", "", selected)
        
        available = [t['theme'] for t in themes]
        if selected in available:
            print(f"[theme_selection] LLM selected theme: {selected}")
            return get_theme(selected)
    except Exception as e:
        print(f"[theme_selection] Error calling LLM for theme selection: {e}. Falling back to default.")

    # Fallback to frankfurt or seriph or scholarly (prioritizing frankfurt for premium styling)
    available = {theme.get('theme') for theme in themes}
    theme_name = next((name for name in ('frankfurt', 'seriph', 'scholarly') if name in available), None)
    if not theme_name:
        theme_name = next((theme.get('theme') for theme in themes if theme.get('theme')), 'seriph')
    print(f"[theme_selection] Fallback selected theme: {theme_name}")
    return get_theme(theme_name)
