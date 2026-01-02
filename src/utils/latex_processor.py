import re
from typing import List, Tuple


class LaTeXProcessor:
    TRIG_FUNCTIONS = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh']
    MATH_FUNCTIONS = ['log', 'ln', 'exp', 'lim', 'sum', 'prod', 'int', 'sqrt', 'max', 'min', 'sup', 'inf']

    def process_slide_content(self, content: List[str]) -> List[str]:
        return content

    def process_speaker_notes(self, notes: str) -> str:
        return notes


def process_slide_latex(slide_data: dict) -> dict:
    return slide_data


def fix_latex_in_text(text: str) -> str:
    return text
