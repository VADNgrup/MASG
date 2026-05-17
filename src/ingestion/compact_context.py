import re
from pathlib import Path
from typing import Any, Dict, List
from src.utils.config import Config
from src.utils.file_utils import save_json, load_json

_WORD_RE = re.compile(r"[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9_/-]{3,}")
_STOPWORDS = {
    "this", "that", "with", "from", "into", "have", "were", "their", "there", "which", "will",
    "the", "and", "for", "are", "was", "has", "not", "can", "using", "used", "than", "then",
    "các", "những", "được", "trong", "ngoài", "hoặc", "không", "một", "này", "với", "cho",
    "khi", "đến", "từ", "theo", "trên", "dưới", "như", "vào", "của", "là", "và",
}

def compact_context_path(document_id: str) -> Path:
    return Config.CONTEXT_DIR / f"{document_id}_compact.json"

def load_compact_context(document_id: str) -> Dict[str, Any] | None:
    path = compact_context_path(document_id)
    if not path.exists():
        return None
    return load_json(path)

def save_compact_context(compact: Dict[str, Any]) -> Path:
    path = compact_context_path(compact["document_id"])
    save_json(compact, path)
    return path

def build_compact_context(document_id: str, source_file: str, markdown: str, page_count: int) -> Dict[str, Any]:
    pages = _split_pages(markdown)
    page_cards = [_page_card(page_num, page_md) for page_num, page_md in pages]
    sections = _section_map(page_cards)
    return {
        "schema_version": 3,
        "document_id": document_id,
        "source_file": source_file,
        "page_count": page_count,
        "document_summary": _document_summary(page_cards),
        "section_map": sections,
        "page_cards": page_cards,
        "asset_manifest": _asset_manifest(page_cards),
    }

def ensure_compact_context(context) -> Dict[str, Any]:
    compact = load_compact_context(context.document_id)
    if compact is not None and compact.get("schema_version") == 3:
        return compact
    compact = build_compact_context(
        document_id=context.document_id,
        source_file=context.source_file,
        markdown=context.text_content.markdown,
        page_count=context.text_content.page_count,
    )
    save_compact_context(compact)
    return compact

def render_compact_context(compact: Dict[str, Any], max_chars: int=12000) -> str:
    parts = [
        f"Document ID: {compact.get('document_id', '')}",
        f"Source file: {compact.get('source_file', '')}",
        f"Pages: {compact.get('page_count', 0)}",
        "",
        "Document summary:",
        compact.get("document_summary", ""),
        "",
        "Section map:",
    ]
    for section in compact.get("section_map", []):
        parts.append(f"- p.{section.get('page', '?')} {section.get('title', '')}: {section.get('summary', '')}")
    parts.append("")
    parts.append("Page cards:")
    for card in compact.get("page_cards", []):
        headings = "; ".join(card.get("headings", [])[:6])
        keywords = ", ".join(card.get("keywords", [])[:10])
        assets = "; ".join(card.get("assets", [])[:5])
        parts.append(f"Page {card.get('page')}:")
        if headings:
            parts.append(f"Headings: {headings}")
        if keywords:
            parts.append(f"Keywords: {keywords}")
        if assets:
            parts.append(f"Assets: {assets}")
        numbered_items = card.get("numbered_items", [])
        if numbered_items:
            parts.append("Numbered items:")
            for item in numbered_items[:12]:
                parts.append(f"{item.get('number')}. {item.get('text', '')}")
        parts.append(card.get("summary", ""))
        parts.append("")
        if len("\n".join(parts)) >= max_chars:
            break
    rendered = "\n".join(parts)
    return rendered[:max_chars]

def _split_pages(markdown: str) -> List[tuple[int, str]]:
    matches = list(re.finditer(r"<!--\s*PAGE\s+(\d+)\s*-->", markdown, flags=re.IGNORECASE))
    if not matches:
        return [(1, markdown)]
    pages = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        pages.append((int(match.group(1)), markdown[start:end].strip()))
    return pages

def _page_card(page_num: int, page_md: str) -> Dict[str, Any]:
    clean = _clean_text(page_md)
    headings = re.findall(r"^#{1,4}\s+(.+)$", page_md, flags=re.MULTILINE)
    assets = _extract_assets(page_md)
    formulas = re.findall(r"\$\$(.*?)\$\$", page_md, flags=re.DOTALL)
    numbered_items = _extract_numbered_items(page_md)
    return {
        "page": page_num,
        "headings": [_squash(h)[:120] for h in headings[:10]],
        "summary": _first_sentences(clean, 900),
        "keywords": _keywords(clean),
        "assets": assets[:12],
        "numbered_items": numbered_items[:30],
        "formula_count": len(formulas),
        "table_count": _count_markdown_tables(page_md),
    }

def _section_map(page_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections = []
    seen = set()
    for card in page_cards:
        headings = card.get("headings") or [f"Page {card.get('page')}"]
        for heading in headings[:3]:
            key = heading.lower()
            if key in seen:
                continue
            seen.add(key)
            sections.append({
                "title": heading,
                "page": card.get("page"),
                "summary": card.get("summary", "")[:500],
                "keywords": card.get("keywords", [])[:8],
            })
    if not sections:
        for card in page_cards:
            sections.append({
                "title": f"Page {card.get('page')}",
                "page": card.get("page"),
                "summary": card.get("summary", "")[:500],
                "keywords": card.get("keywords", [])[:8],
            })
    return sections[:80]

def _asset_manifest(page_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets = []
    for card in page_cards:
        for asset in card.get("assets", []):
            assets.append({"page": card.get("page"), "description": asset})
    return assets

def _document_summary(page_cards: List[Dict[str, Any]]) -> str:
    pieces = []
    for card in page_cards[:12]:
        page = card.get("page")
        summary = card.get("summary", "")
        if summary:
            pieces.append(f"Page {page}: {summary}")
        numbered_items = card.get("numbered_items", [])
        if numbered_items:
            items = " ".join(f"{item.get('number')}. {item.get('text', '')}" for item in numbered_items[:10])
            pieces.append(f"Page {page} numbered items: {items}")
    return "\n".join(pieces)[:5000]

def _extract_numbered_items(page_md: str) -> List[Dict[str, Any]]:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", page_md)
    text = re.sub(r"\*(?:Figure|Table|Fig\.?|Bảng|Hình)[:\s]+[^*]+\*", " ", text, flags=re.IGNORECASE)
    pattern = re.compile(r"(?ms)(?:^|\n|\s)(\d{1,2})\.\s+(.+?)(?=(?:\n|\s)\d{1,2}\.\s+|\n\s*!\[|\n\s*---|\Z)")
    items = []
    for number, body in pattern.findall(text):
        clean = _squash(body)
        if len(clean) < 20:
            continue
        items.append({"number": int(number), "text": clean[:700]})
    return items

def _extract_assets(page_md: str) -> List[str]:
    assets = []
    for alt, path in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", page_md):
        text = _squash(alt or path)
        if text:
            assets.append(text[:180])
    for caption in re.findall(r"\*(?:Figure|Table|Fig\.?|Bảng|Hình)[:\s]+([^*]+)\*", page_md, flags=re.IGNORECASE):
        text = _squash(caption)
        if text:
            assets.append(text[:180])
    return assets

def _count_markdown_tables(page_md: str) -> int:
    return len(re.findall(r"^\s*\|.+\|\s*$\n^\s*\|[-:\s|]+\|\s*$", page_md, flags=re.MULTILINE))

def _keywords(text: str) -> List[str]:
    counts: Dict[str, int] = {}
    for word in _WORD_RE.findall(text):
        key = word.lower().strip("_-/")
        if len(key) < 4 or key in _STOPWORDS:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:16]]

def _clean_text(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"`{3}.*?`{3}", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return _squash(text)

def _first_sentences(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    result = ""
    for sentence in sentences:
        if len(result) + len(sentence) + 1 > max_chars:
            break
        result = f"{result} {sentence}".strip()
    return result or text[:max_chars]

def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()
