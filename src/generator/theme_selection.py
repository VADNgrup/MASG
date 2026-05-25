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
        
    prompt = f"""You are a presentation design expert. Select the single best theme for the lecture outline below.

Choose based on SUBJECT MATTER and TONE:
- 'frankfurt': structured multi-topic lectures (4+ numbered chapters); law, management, economics, social sciences. DEFAULT for most standard university lectures.
- 'umn': university STEM lectures (math, physics, chemistry, biology, engineering, CS, statistics) where an energetic, branded style fits the audience. NOT for general or non-STEM topics.
- 'seriph': humanities, language, literature, philosophy, history, arts; minimalism and readability are priority.
- 'scholarly': ONLY for research paper presentations, thesis defenses, scientific journal reports with dense argumentation. NOT standard course lectures.
- 'improving-25': technology trends, innovation, startup/business strategy, industry-focused topics.
- 'bricks': ONLY primary/secondary school content for young students.
- 'meetup': ONLY informal community events or workshops, never academic.

If unsure, prefer 'frankfurt' for academic lectures or 'seriph' for general content.

Lecture Outline:
\"\"\"
{outline_md}
\"\"\"

Respond with ONLY the theme name in lowercase (e.g. 'frankfurt'). No explanation."""

    try:
        messages = [{"role": "user", "content": prompt}]
        selected = chat(model=model, messages=messages, temperature=0.1).strip().lower()
        selected = re.sub(r"[^a-z0-9_-]", "", selected)
        
        available = [t['theme'] for t in themes]
        if selected in available:
            print(f"[theme_selection] LLM selected theme: {selected}")
            return get_theme(selected)
    except Exception as e:
        print(f"[theme_selection] Error calling LLM for theme selection: {e}. Falling back to default.")

    available = {theme.get('theme') for theme in themes}
    theme_name = next((name for name in ('frankfurt', 'seriph', 'scholarly') if name in available), None)
    if not theme_name:
        theme_name = next((theme.get('theme') for theme in themes if theme.get('theme')), 'seriph')
    print(f"[theme_selection] Fallback selected theme: {theme_name}")
    return get_theme(theme_name)
