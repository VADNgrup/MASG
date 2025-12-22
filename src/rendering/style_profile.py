from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class BlockStyle:
    surface: str
    label_class: str
    body_class: str
    label_text: str


BLOCK_STYLES: Dict[str, BlockStyle] = {
    "key_concept": BlockStyle(
        surface="p-5 rounded-3xl bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-100 shadow-sm",
        label_class="text-xs font-semibold tracking-wide text-sky-700 uppercase",
        body_class="mt-2 text-[1.05rem] leading-relaxed text-slate-800",
        label_text="KHÁI NIỆM CHÍNH",
    ),
    "formula": BlockStyle(
        surface="p-5 rounded-3xl bg-slate-900 text-slate-50 shadow-lg",
        label_class="text-xs font-semibold tracking-[0.18em] text-sky-300 uppercase",
        body_class="mt-3 text-[1.05rem] leading-relaxed text-slate-50",
        label_text="CÔNG THỨC",
    ),
    "example": BlockStyle(
        surface="p-5 rounded-3xl bg-gradient-to-r from-amber-50 to-rose-50 border border-amber-100 shadow-sm",
        label_class="text-xs font-semibold tracking-wide text-amber-700 uppercase",
        body_class="mt-2 text-[1.02rem] leading-relaxed text-slate-800",
        label_text="VÍ DỤ",
    ),
    "property": BlockStyle(
        surface="p-5 rounded-3xl bg-emerald-50 border border-emerald-100 shadow-sm",
        label_class="text-xs font-semibold tracking-wide text-emerald-700 uppercase",
        body_class="mt-2 text-[1.02rem] leading-relaxed text-slate-800",
        label_text="TÍNH CHẤT",
    ),
    "important": BlockStyle(
        surface="p-5 rounded-3xl bg-amber-50 border-l-4 border-amber-500 shadow-sm",
        label_class="text-xs font-semibold tracking-wide text-amber-800 uppercase",
        body_class="mt-2 text-[1.02rem] leading-relaxed text-slate-900",
        label_text="LƯU Ý QUAN TRỌNG",
    ),
    "note": BlockStyle(
        surface="p-4 rounded-2xl bg-slate-50 border border-slate-200",
        label_class="text-xs font-semibold tracking-wide text-slate-600 uppercase",
        body_class="mt-1 text-[1rem] leading-relaxed text-slate-800",
        label_text="GHI CHÚ",
    ),
    "other": BlockStyle(
        surface="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm",
        label_class="text-xs font-semibold tracking-wide text-slate-500 uppercase",
        body_class="mt-1 text-[1.02rem] leading-relaxed text-slate-900",
        label_text="NỘI DUNG",
    ),
}


def get_block_style(content_type: str) -> BlockStyle:
    return BLOCK_STYLES.get(content_type, BLOCK_STYLES["other"])


