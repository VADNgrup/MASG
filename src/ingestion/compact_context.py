import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.utils.config import Config
from src.utils.file_utils import load_json, save_json
from src.utils.language_utils import detect_language_code
from src.utils.llm import chat

SCHEMA_VERSION = 16
_WORD_RE = re.compile(r"[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ0-9_/-]{2,}")

_QUALITATIVE_FLOAT = {"high": 0.9, "medium": 0.6, "moderate": 0.6, "low": 0.3, "none": 0.0}

def _safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    lower = str(val).strip().lower()
    if lower in _QUALITATIVE_FLOAT:
        return _QUALITATIVE_FLOAT[lower]
    try:
        return float(lower)
    except (ValueError, TypeError):
        return default
_SIZE_ONLY_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*(?:kb|mb|gb|tb)(?:\s*\([^)]*\))?\s*$", re.IGNORECASE)
_URL_RE = re.compile(r"https?://|www\.|doi\.org|doi:", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_CITATION_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_STOPWORDS = {
    "this", "that", "with", "from", "into", "have", "were", "their", "there", "which", "will",
    "the", "and", "for", "are", "was", "has", "not", "can", "using", "used", "than", "then",
    "các", "những", "được", "trong", "ngoài", "hoặc", "không", "một", "này", "với", "cho",
    "khi", "đến", "từ", "theo", "trên", "dưới", "như", "vào", "của", "là", "và",
}
_TRAILING_TRIM_WORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "from", "with", "by", "as",
    "and", "or", "but", "that", "which", "whose", "its", "their", "these", "this", "those",
    "newly", "recently", "very", "quite", "rather", "also", "even", "just",
}
_STRUCTURAL_HEADING_RE = re.compile(
    r"^(?:"
    r"[IVXivx]{1,8}\.?\s*$"
    r"|"
    r"(?:chương|phần|mục|bài|tiết|chapter|part|section|unit|lesson|module|topic|appendix|annex"
    r"|bölüm|kapitel|chapitre|partie|cap[ií]tulo|sezione|hoofdstuk|rozdzia[lł]|lección|leçon)\s*"
    r"(?:\d+(?:[.\-]\d+)*|[IVXivx]{1,8})"
    r"(?:\s*[.:;].*)?$"
    r"|"
    r"第\s*(?:\d+(?:[.\-]\d+)*|[一二三四五六七八九十百千]+)\s*"
    r"(?:章|節|节|部分|部份|篇|單元|单元|课|課)?"
    r"(?:\s*[.：、。].*)?$"
    r"|"
    r"제\s*\d+\s*(?:장|절|부|편)?"
    r"(?:\s*[.：、].*)?$"
    r"|"
    r"(?:บท|ตอน|ส่วน)(?:ที่)?\s*\d+"
    r"(?:\s*[.:：].*)?$"
    r")",
    re.IGNORECASE | re.UNICODE,
)

_NOISE_PREFIXES = (
    "cite this document as",
    "references",
    "acknowledgement",
    "acknowledgements",
    "acknowledgment",
    "acknowledgments",
    "funding",
    "conflict of interest",
    "last retrieved",
    "retrieved from",
    "keywords",
    "key words",
    "target audience",
    "author",
    "authors",
    "affiliation",
    "contact",
    "doi",
)


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


def build_compact_context(
    document_id: str,
    source_file: str,
    markdown: str,
    page_count: int,
    page_insights: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    pages = _split_pages(markdown)
    page_cards = [_page_card(page_num, page_md) for page_num, page_md in pages]
    normalized_page_insights = _normalise_page_insights(page_insights, page_count, page_cards)
    section_map = _section_map(pages, normalized_page_insights)
    content_units = _content_units(pages, normalized_page_insights)
    profile = _document_profile(document_id, source_file, page_cards, content_units, normalized_page_insights)
    primary_subject = _primary_subject(document_id, source_file, section_map, normalized_page_insights)
    document_language = _document_language(markdown, normalized_page_insights, section_map)
    must_have_points = _must_have_points(
        document_id=document_id,
        source_file=source_file,
        markdown=markdown,
        profile=profile,
        content_units=content_units,
        page_insights=normalized_page_insights,
        section_map=section_map,
        document_language=document_language,
    )
    document_insights = _document_insights(
        document_id=document_id,
        source_file=source_file,
        profile=profile,
        primary_subject=primary_subject,
        document_language=document_language,
        page_insights=normalized_page_insights,
        must_have_points=must_have_points,
        content_units=content_units,
        section_map=section_map,
        markdown=markdown,
    )
    presentation_units = _presentation_units(content_units, must_have_points)
    return {
        "schema_version": SCHEMA_VERSION,
        "document_id": document_id,
        "source_file": source_file,
        "page_count": page_count,
        "document_summary": _document_summary(page_cards, normalized_page_insights),
        "document_profile": profile,
        "document_language": document_language,
        "primary_subject": primary_subject,
        "section_map": section_map,
        "page_cards": page_cards,
        "page_insights": normalized_page_insights,
        "content_units": content_units,
        "presentation_units": presentation_units,
        "must_have_points": must_have_points,
        "document_insights": document_insights,
        "asset_manifest": _asset_manifest(page_cards),
    }


def ensure_compact_context(context) -> Dict[str, Any]:
    compact = load_compact_context(context.document_id)
    if compact is not None and compact.get("schema_version") == SCHEMA_VERSION:
        return compact
    compact = build_compact_context(
        document_id=context.document_id,
        source_file=context.source_file,
        markdown=context.text_content.markdown,
        page_count=context.text_content.page_count,
        page_insights=[item.model_dump() if hasattr(item, "model_dump") else item for item in getattr(context, "page_insights", [])],
    )
    save_compact_context(compact)
    return compact


def render_compact_context(compact: Dict[str, Any], max_chars: int = 12000) -> str:
    profile = compact.get("document_profile", {})
    parts = [
        f"Document ID: {compact.get('document_id', '')}",
        f"Source file: {compact.get('source_file', '')}",
        f"Pages: {compact.get('page_count', 0)}",
        f"Primary subject: {compact.get('primary_subject', '')}",
        f"Document regime: {profile.get('document_regime', 'sectioned_document')}",
        f"Document language: {compact.get('document_language', 'en')}",
        "",
        "Document insights:",
        f"Title hint: {compact.get('document_insights', {}).get('suggested_title', '')}",
        f"Thesis: {compact.get('document_insights', {}).get('document_thesis', '')}",
        "",
        "Document summary:",
        compact.get("document_summary", ""),
        "",
        "Must-have points:",
    ]
    for point in compact.get("must_have_points", [])[:8]:
        parts.append(f"- {point.get('label', '')}: {point.get('summary', '')}")
    parts.append("")
    parts.append("Presentation units:")
    for unit in compact.get("presentation_units", [])[:16]:
        prefix = "[slideworthy]" if unit.get("slideworthy") else "[support]"
        parts.append(
            f"- {prefix} p.{_first_source_page(unit)} {unit.get('type', '')} | {unit.get('outline_label', unit.get('title', ''))}: "
            f"{unit.get('summary', '')}"
        )
    parts.append("")
    parts.append("Page insights:")
    for insight in compact.get("page_insights", [])[: min(8, compact.get("page_count", 0) or 8)]:
        must = "; ".join(insight.get("must_have_points", [])[:4])
        parts.append(f"- p.{insight.get('page')}: {insight.get('page_title', '')} [{insight.get('page_role', '')}] {must}")
    rendered = "\n".join(parts)
    return rendered[:max_chars]


def _split_pages(markdown: str) -> List[Tuple[int, str]]:
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
    numbered_items = _extract_numbered_items(page_md)
    tables = _extract_markdown_tables(page_md)
    return {
        "page": page_num,
        "headings": [_squash(h)[:140] for h in headings[:10]],
        "summary": _first_sentences(clean, 800),
        "keywords": _keywords(clean),
        "assets": _extract_assets(page_md)[:12],
        "numbered_items": numbered_items[:30],
        "table_count": len(tables),
        "formula_count": len(re.findall(r"\$\$(.*?)\$\$", page_md, flags=re.DOTALL)),
        "lines": [line.strip() for line in page_md.splitlines() if line.strip()][:120],
    }


def _strip_md_images(text: str) -> str:
    return re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text or '').strip()




def _normalise_page_insights(page_insights: List[Dict[str, Any]] | None, page_count: int, page_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    doc_sample = " ".join(card.get("summary", "") for card in page_cards[:10])
    doc_script = detect_language_code(doc_sample)

    def _filter_points(items) -> List[str]:
        result = []
        for item in items:
            text = _squash(item)
            if not text:
                continue
            if doc_script == "latin" and detect_language_code(text) not in ("latin", "unknown"):
                continue
            result.append(text[:180])
        return result[:8]

    by_page: Dict[int, Dict[str, Any]] = {}
    for raw in page_insights or []:
        if not isinstance(raw, dict):
            continue
        page = int(raw.get("page") or 0)
        if page <= 0:
            continue
        by_page[page] = {
            "page": page,
            "page_role": str(raw.get("page_role") or "content").strip() or "content",
            "page_title": _squash(_strip_md_images(raw.get("page_title", "")))[:180],
            "must_have_points": _filter_points(raw.get("must_have_points", [])),
            "support_points": [_squash(item)[:180] for item in raw.get("support_points", []) if _squash(item)][:8],
            "noise_points": [_squash(item)[:180] for item in raw.get("noise_points", []) if _squash(item)][:8],
            "confidence": _safe_float(raw.get("confidence"), 0.0),
        }
    normalised = []
    for page in range(1, page_count + 1):
        if page in by_page:
            normalised.append(by_page[page])
            continue
        card = next((item for item in page_cards if item.get("page") == page), None)
        title = ""
        if card and card.get("headings"):
            title = card["headings"][0]
        normalised.append({
            "page": page,
            "page_role": "content",
            "page_title": title,
            "must_have_points": [],
            "support_points": [],
            "noise_points": [],
            "confidence": 0.0,
        })
    return normalised


def _section_map(pages: List[Tuple[int, str]], page_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    seen = set()
    insight_by_page = {item["page"]: item for item in page_insights}
    for page_num, page_md in pages:
        insight = insight_by_page.get(page_num, {})
        headings = re.findall(r"^#{1,4}\s+(.+)$", page_md, flags=re.MULTILINE)
        candidates = headings[:4] or ([insight.get("page_title")] if insight.get("page_title") else [])
        for title in candidates:
            clean_title = _squash(title)[:140]
            if not clean_title or _is_noise_text(clean_title) or _is_structural_heading_only(clean_title):
                continue
            key = clean_title.lower()
            if key in seen:
                continue
            seen.add(key)
            sections.append({
                "title": clean_title,
                "page": page_num,
                "keywords": _keywords(_clean_text(page_md))[:8],
            })
    if not sections:
        for page_num, page_md in pages[: min(8, len(pages))]:
            sections.append({
                "title": f"Page {page_num}",
                "page": page_num,
                "keywords": _keywords(_clean_text(page_md))[:8],
            })
    return sections[:80]


def _content_units(pages: List[Tuple[int, str]], page_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    counter = 1
    insight_by_page = {item["page"]: item for item in page_insights}
    for page_num, page_md in pages:
        insight = insight_by_page.get(page_num, {})
        page_clean = _clean_text(page_md)
        sections = _section_units(page_num, page_md)
        if insight.get("page_title") and not _is_noise_text(insight["page_title"]):
            units.append(_make_unit(
                counter,
                "page_focus",
                insight["page_title"],
                _page_focus_summary(page_md, page_clean),
                [page_num],
                quality="support" if len(sections) >= 2 else "core",
                outline_label=_outline_label(insight["page_title"]),
            ))
            counter += 1
        for title, body in sections:
            if _is_noise_text(title) or _is_metadata_noise(body) or _is_structural_heading_only(title):
                continue
            semantic_blocks = _semantic_subunits(title, body)
            units.append(_make_unit(
                counter,
                "section",
                title,
                _first_sentences(_clean_text(body), 320),
                [page_num],
                quality="support" if len(semantic_blocks) >= 2 else "core",
                outline_label=_outline_label(title),
            ))
            counter += 1
            for block in semantic_blocks:
                units.append(_make_unit(
                    counter,
                    block["type"],
                    block["title"],
                    block["summary"],
                    [page_num],
                    quality=block["quality"],
                    outline_label=block.get("outline_label") or _outline_label(block["title"]),
                ))
                counter += 1
        for item in _extract_numbered_items(page_md):
            text = _squash(item.get("text", ""))
            if _is_noise_text(text):
                continue
            number = int(item["number"])
            title = f"Item {number}"
            units.append(_make_unit(
                counter,
                "numbered_item",
                title,
                text[:320],
                [page_num],
                quality="core",
                number=number,
                outline_label=_outline_label(text),
            ))
            counter += 1
        for table in _extract_markdown_tables(page_md):
            for row_title, row_summary in _table_row_units(table):
                if _is_noise_text(row_title) or _looks_like_data_cell_title(row_title):
                    continue
                units.append(_make_unit(
                    counter,
                    "table_row",
                    row_title,
                    row_summary[:320],
                    [page_num],
                    quality="support" if _looks_supportish(row_title, row_summary) else "core",
                    outline_label=_outline_label(row_title),
                ))
                counter += 1
        for point in insight.get("must_have_points", []):
            if _is_noise_text(point):
                continue
            units.append(_make_unit(
                counter,
                "must_have_hint",
                point,
                point,
                [page_num],
                quality="core",
                outline_label=_outline_label(point),
            ))
            counter += 1
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for unit in units:
        key = (unit.get("type"), unit.get("title", "").lower(), unit.get("summary", "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(unit)
    for unit in deduped:
        unit["salience_score"] = _base_salience(unit, page_insights)
    return deduped


def _section_units(page_num: int, page_md: str) -> List[Tuple[str, str]]:
    matches = list(re.finditer(r"^#{1,4}\s+(.+)$", page_md, flags=re.MULTILINE))
    sections: List[Tuple[str, str]] = []
    if not matches:
        page_text = _clean_text(page_md)
        if page_text:
            sections.append((f"Page {page_num}", page_text))
        return sections
    for idx, match in enumerate(matches):
        title = _squash(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(page_md)
        body = page_md[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def _semantic_subunits(section_title: str, body: str) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    candidates.extend(_bold_block_subunits(section_title, body))
    candidates.extend(_bullet_subunits(section_title, body))
    candidates.extend(_single_column_table_subunits(section_title, body))
    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in candidates:
        title = _outline_label(item.get("title", ""))
        summary = _first_sentences(_clean_text(item.get("summary", "")), 320)
        if not title or _is_noise_text(title) or _is_metadata_noise(summary):
            continue
        if title.lower() == _outline_label(section_title).lower():
            continue
        key = (item.get("type", "detail_block"), title.lower(), summary.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append({
            "type": item.get("type", "detail_block"),
            "title": title,
            "summary": summary,
            "quality": item.get("quality", "core"),
            "outline_label": _outline_label(title),
        })
    return deduped[:8]


def _bold_block_subunits(section_title: str, body: str) -> List[Dict[str, str]]:
    lines = [line.rstrip() for line in body.splitlines()]
    blocks: List[Dict[str, str]] = []
    current_title = ""
    current_lines: List[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            continue
        bold_match = re.fullmatch(r"\*\*(.+?)\*\*", line)
        if bold_match:
            if current_title and current_lines:
                blocks.append({
                    "type": "detail_block",
                    "title": current_title,
                    "summary": " ".join(current_lines),
                    "quality": "core",
                })
            current_title = _squash(bold_match.group(1))
            current_lines = []
            continue
        if current_title:
            if line.startswith("|") and line.endswith("|"):
                continue
            clean = _squash(re.sub(r"^[*-]\s*", "", line))
            if clean:
                current_lines.append(clean)
    if current_title and current_lines:
        blocks.append({
            "type": "detail_block",
            "title": current_title,
            "summary": " ".join(current_lines),
            "quality": "core",
        })
    return [block for block in blocks if _is_meaningful_subunit(section_title, block["title"], block["summary"])]


def _bullet_subunits(section_title: str, body: str) -> List[Dict[str, str]]:
    bullets: List[Dict[str, str]] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not re.match(r"^[*-]\s+", line):
            continue
        clean = _squash(re.sub(r"^[*-]\s+", "", line))
        if not clean or _URL_RE.fullmatch(clean):
            continue
        title = _bullet_title(clean)
        bullets.append({
            "type": "detail_bullet",
            "title": title,
            "summary": clean,
            "quality": "support" if _looks_supportish(title, clean) else "core",
        })
    return [item for item in bullets if _is_meaningful_subunit(section_title, item["title"], item["summary"])]


def _single_column_table_subunits(section_title: str, body: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for table in _extract_markdown_tables(body):
        lines = [line.strip() for line in table.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        header = [_squash(cell) for cell in lines[0].strip("|").split("|")]
        if len(header) != 1:
            continue
        for row_line in lines[2:]:
            cells = [_squash(cell) for cell in row_line.strip("|").split("|")]
            if len(cells) != 1:
                continue
            cell = cells[0]
            if not cell or _is_noise_text(cell) or _looks_like_data_cell_title(cell):
                continue
            items.append({
                "type": "detail_row",
                "title": _single_cell_title(cell),
                "summary": cell,
                "quality": "core",
            })
    return [item for item in items if _is_meaningful_subunit(section_title, item["title"], item["summary"])]


def _is_meaningful_subunit(section_title: str, title: str, summary: str) -> bool:
    title_terms = set(_WORD_RE.findall(_outline_label(title).lower()))
    section_terms = set(_WORD_RE.findall(_outline_label(section_title).lower()))
    if not title_terms and not summary:
        return False
    if len(_squash(summary)) < 18:
        return False
    if title_terms and section_terms and title_terms <= section_terms and len(title_terms) <= 2:
        return False
    return True


def _bullet_title(text: str) -> str:
    if ":" in text:
        left, right = text.split(":", 1)
        if 1 <= len(left.split()) <= 8 and len(right.strip()) >= 6:
            return _squash(left)
    words = _squash(text).split()
    return " ".join(words[:8])


def _single_cell_title(text: str) -> str:
    if ":" in text:
        left, _ = text.split(":", 1)
        if 1 <= len(left.split()) <= 8:
            return _squash(left)
    words = _squash(text).split()
    return " ".join(words[:10])


def _page_focus_summary(page_md: str, page_clean: str) -> str:
    lines = []
    for raw in page_md.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("![") or line.startswith("<!--"):
            continue
        if line.startswith("|") and line.endswith("|"):
            continue
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        line = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", line)
        line = _squash(line)
        if not line or _is_noise_text(line):
            continue
        lines.append(line)
        if len(lines) >= 3 or len(" ".join(lines)) >= 200:
            break
    if lines:
        return _first_sentences(" ".join(lines), 220)
    return _first_sentences(page_clean, 220)


def _document_profile(
    document_id: str,
    source_file: str,
    page_cards: List[Dict[str, Any]],
    content_units: List[Dict[str, Any]],
    page_insights: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_numbered = sum(len(card.get("numbered_items", [])) for card in page_cards)
    total_tables = sum(card.get("table_count", 0) for card in page_cards)
    reference_score = 0
    for card in page_cards:
        summary = (card.get("summary") or "").lower()
        if _URL_RE.search(summary):
            reference_score += 2
        if summary.count("(") >= 2 and _CITATION_RE.search(summary):
            reference_score += 1
    if reference_score >= 4 and total_numbered < 8:
        regime = "reference_heavy_document"
    elif total_numbered >= 6:
        regime = "numbered_principles_document"
    elif total_tables >= 2 and not any(unit.get("type") == "section" and len(unit.get("summary", "")) > 240 for unit in content_units):
        regime = "table_heavy_document"
    elif reference_score >= 4:
        regime = "reference_heavy_document"
    else:
        regime = "sectioned_document"
    return {
        "document_regime": regime,
        "signals": {
            "table_count": total_tables,
            "numbered_item_count": total_numbered,
            "reference_score": reference_score,
            "page_insight_confidence": round(sum(item.get("confidence", 0.0) for item in page_insights) / max(1, len(page_insights)), 3),
            "unit_count": len(content_units),
        },
    }


def _primary_subject(document_id: str, source_file: str, section_map: List[Dict[str, Any]], page_insights: List[Dict[str, Any]]) -> str:
    stem = Path(source_file or document_id).stem.replace("_", " ").replace("-", " ")
    stem = _squash(stem)
    early_sections = [section.get("title", "") for section in section_map[:5] if section.get("title")]
    for title in early_sections:
        clean = _outline_label(title)
        if clean and not _is_noise_text(clean) and not _is_generic_subject(clean):
            return clean
    early_titles = []
    for insight in page_insights[:3]:
        if insight.get("page_title") and not _is_noise_text(insight["page_title"]):
            early_titles.append(insight["page_title"])
    for section in section_map[:5]:
        if section.get("title") and not _is_noise_text(section["title"]):
            early_titles.append(section["title"])
    for title in early_titles:
        clean = _outline_label(title)
        if clean and not _is_generic_subject(clean):
            return clean
    return stem


def _document_language(markdown: str, page_insights: List[Dict[str, Any]], section_map: List[Dict[str, Any]]) -> str:
    samples = []
    samples.extend(insight.get("page_title", "") for insight in page_insights[:4])
    for insight in page_insights[:4]:
        samples.extend(insight.get("must_have_points", [])[:3])
    samples.extend(section.get("title", "") for section in section_map[:6])
    samples.append(markdown[:2000])
    return detect_language_code(" ".join(sample for sample in samples if sample))


def _clean_must_have_labels(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    for p in points:
        label = _squash(_strip_md_images(p.get("label", "")))
        if label:
            cleaned.append({**p, "label": label})
    return cleaned


def _must_have_points(
    document_id: str,
    source_file: str,
    markdown: str,
    profile: Dict[str, Any],
    content_units: List[Dict[str, Any]],
    page_insights: List[Dict[str, Any]],
    section_map: List[Dict[str, Any]],
    document_language: str,
) -> List[Dict[str, Any]]:
    regime = profile.get("document_regime", "sectioned_document")
    if regime in {"numbered_principles_document", "table_heavy_document"}:
        return _fallback_must_have_points(content_units, page_insights, regime)
    prompt = _must_have_prompt(document_id, source_file, profile, page_insights, section_map, document_language)
    suggestions = _llm_must_have_points(prompt)
    units_by_id = {unit["unit_id"]: unit for unit in content_units}
    selected: List[Dict[str, Any]] = []
    seen_units: set[str] = set()
    for suggestion in suggestions:
        matched = _match_suggestion_to_units(suggestion, content_units)
        if not matched:
            continue
        anchor = matched[0]
        if anchor["unit_id"] in seen_units:
            continue
        seen_units.add(anchor["unit_id"])
        raw_label = anchor.get("outline_label") or suggestion.get("label") or anchor.get("title") or ""
        label = _squash(_strip_md_images(raw_label))
        if not label:
            continue
        selected.append({
            "point_id": f"mh{len(selected) + 1:02d}",
            "label": label,
            "summary": suggestion.get("summary") or anchor.get("summary"),
            "source_unit_ids": [unit["unit_id"] for unit in matched[:3]],
            "source_pages": sorted({page for unit in matched[:3] for page in unit.get("source_pages", [])}),
            "salience_score": round(max(unit.get("salience_score", 0.0) for unit in matched[:3]), 3),
            "number": anchor.get("number"),
        })
    if len(selected) >= 3:
        enriched = _augment_diverse_points(selected[:8], content_units)
        return _clean_must_have_labels(_ensure_evidence_rich_coverage(enriched[:8], content_units)[:8])
    return _clean_must_have_labels(_fallback_must_have_points(content_units, page_insights, profile.get("document_regime", "sectioned_document")))


def _presentation_units(content_units: List[Dict[str, Any]], must_have_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    must_have_ids = {unit_id for point in must_have_points for unit_id in point.get("source_unit_ids", [])}
    presentation = []
    for unit in content_units:
        cloned = dict(unit)
        parent_like_section = cloned.get("type") == "section" and cloned.get("quality") == "support"
        cloned["slideworthy"] = (not parent_like_section) and (
            cloned["unit_id"] in must_have_ids or cloned.get("salience_score", 0.0) >= 0.62
        )
        if cloned["unit_id"] in must_have_ids:
            cloned["presentation_role"] = "topic_candidate"
        elif parent_like_section:
            cloned["presentation_role"] = "support_candidate"
        elif cloned.get("quality") == "support":
            cloned["presentation_role"] = "detail_candidate"
        else:
            cloned["presentation_role"] = "support_candidate"
        presentation.append(cloned)
    presentation.sort(key=lambda item: (-float(item.get("salience_score", 0.0)), _first_source_page(item), item.get("title", "")))
    return presentation


def _document_insights(
    document_id: str,
    source_file: str,
    profile: Dict[str, Any],
    primary_subject: str,
    document_language: str,
    page_insights: List[Dict[str, Any]],
    must_have_points: List[Dict[str, Any]],
    content_units: List[Dict[str, Any]],
    section_map: List[Dict[str, Any]],
    markdown: str = "",
) -> Dict[str, Any]:
    fallback = _fallback_document_insights(primary_subject, document_language, profile.get("document_regime", "sectioned_document"), must_have_points, section_map)
    prompt = _document_insights_prompt(document_id, source_file, profile, primary_subject, document_language, page_insights, must_have_points, content_units, section_map, markdown)
    parsed = _llm_document_insights(prompt)
    if not parsed:
        return fallback
    suggested_outline = [_strip_md_images(item).strip() for item in parsed.get("suggested_outline", []) if item]
    suggested_outline = [item for item in suggested_outline if item and not _is_noise_text(item)]
    if not suggested_outline:
        suggested_outline = fallback["suggested_outline"]
    suggested_outline = _ensure_outline_covers_must_have(suggested_outline, must_have_points)
    suggested_title = _strip_md_images(parsed.get("suggested_title") or "").strip() or fallback["suggested_title"]
    thesis = parsed.get("document_thesis") or fallback["document_thesis"]
    narrative_flow = parsed.get("narrative_flow", [])
    if isinstance(narrative_flow, str):
        narrative_flow = [narrative_flow]
    elif not isinstance(narrative_flow, list):
        narrative_flow = []
    return {
        "document_thesis": _squash(thesis)[:280],
        "suggested_title": _squash(suggested_title)[:180],
        "suggested_outline": [_normalize_outline_candidate(item) for item in suggested_outline[:8] if _normalize_outline_candidate(item)],
        "narrative_flow": [_squash(item)[:160] for item in narrative_flow[:8] if _squash(item)],
        "must_include_labels": [_squash(item)[:140] for item in parsed.get("must_include_labels", [])[:8] if _squash(item)],
        "exclude_labels": [_squash(item)[:140] for item in parsed.get("exclude_labels", [])[:8] if _squash(item)],
        "confidence": _safe_float(parsed.get("confidence"), fallback["confidence"]),
    }


def _ensure_outline_covers_must_have(outline: List[str], must_have_points: List[Dict[str, Any]]) -> List[str]:
    normalized = [_normalize_outline_candidate(item) for item in outline if _normalize_outline_candidate(item)]
    outline_terms = set(_WORD_RE.findall(" ".join(normalized).lower()))
    enriched = list(normalized)
    for point in must_have_points:
        label = _normalize_outline_candidate(_strip_md_images(point.get("label", "")))
        if not label:
            continue
        label_terms = set(_WORD_RE.findall(label.lower()))
        if label_terms and outline_terms and (label_terms & outline_terms):
            continue
        if label not in enriched:
            enriched.append(label)
        if len(enriched) >= 8:
            break
    return enriched[:8]


def _fallback_document_insights(primary_subject: str, document_language: str, regime: str, must_have_points: List[Dict[str, Any]], section_map: List[Dict[str, Any]]) -> Dict[str, Any]:
    labels = [point.get("label", "") for point in must_have_points if point.get("label")]
    if regime == "numbered_principles_document":
        if len(labels) >= 6:
            outline = ["1-3", "4-6", "7-10"]
        else:
            outline = labels[:4]
    elif regime == "table_heavy_document":
        meta = [label for label in labels if any(term in label.lower() for term in ["overview", "summary", "tổng quan", "time", "schedule", "format"])]
        topics = [label for label in labels if label not in meta]
        outline = (meta[:1] + topics[:5]) or labels[:6]
    else:
        outline = labels[:6] or [section.get("title", "") for section in section_map[:6]]
    title = primary_subject or (outline[0] if outline else "Generated Lecture")
    thesis = labels[0] if labels else title
    return {
        "document_thesis": thesis,
        "suggested_title": title,
        "suggested_outline": [_normalize_outline_candidate(item) for item in outline if _normalize_outline_candidate(item)],
        "narrative_flow": [],
        "must_include_labels": labels[:6],
        "exclude_labels": [],
        "confidence": 0.35,
    }


def _document_insights_prompt(
    document_id: str,
    source_file: str,
    profile: Dict[str, Any],
    primary_subject: str,
    document_language: str,
    page_insights: List[Dict[str, Any]],
    must_have_points: List[Dict[str, Any]],
    content_units: List[Dict[str, Any]],
    section_map: List[Dict[str, Any]],
    markdown: str = "",
) -> str:
    page_lines = []
    for insight in page_insights[:10]:
        page_lines.append(
            f"- p.{insight.get('page')} {insight.get('page_title', '')} | must-have={insight.get('must_have_points', [])[:4]} | noise={insight.get('noise_points', [])[:3]}"
        )
    must_lines = [f"- {point.get('label')}: {point.get('summary')}" for point in must_have_points[:8]]
    unit_lines = [
        f"- p.{_first_source_page(unit)} {unit.get('type')} | {unit.get('outline_label') or unit.get('title')}: {unit.get('summary')}"
        for unit in sorted(
            content_units,
            key=lambda item: (
                -(float(item.get("salience_score", 0.0)) + _evidence_richness_bonus(item)),
                _first_source_page(item),
                item.get("title", ""),
            ),
        )[:12]
        if not _looks_noise_unit_for_prompt(unit)
    ]
    section_lines = [f"- p.{item.get('page')} {item.get('title')}" for item in section_map[:10]]
    body_sample = _body_text_sample(markdown, max_chars=1200) if markdown else ""
    body_lang_hint = _detect_body_language_hint(body_sample)
    if body_lang_hint:
        lang_rule = (
            f"- CRITICAL LANGUAGE RULE: The document body text is written in {body_lang_hint}. "
            f"You MUST write ALL outputs — document_thesis, suggested_title, suggested_outline, narrative_flow, must_include_labels — in {body_lang_hint} ONLY. "
            f"Do NOT use any other language. Ignore any non-{body_lang_hint} text in section headings or page insights — those are extraction errors."
        )
    else:
        lang_rule = (
            "- CRITICAL LANGUAGE RULE: Identify the language of the DOCUMENT BODY SAMPLE below (paragraph sentences only, ignore headings). "
            "Write ALL outputs in that exact body text language. Do not use any other language."
        )
    body_section = f"DOCUMENT BODY SAMPLE:\n{body_sample}\n\n" if body_sample else ""
    return (
        "You are compiling document-level presentation insights for a slide deck.\n"
        "Return ONLY JSON with keys:\n"
        "document_thesis, suggested_title, suggested_outline, narrative_flow, must_include_labels, exclude_labels, confidence.\n"
        "- confidence must be a float between 0.0 and 1.0 (e.g. 0.8), NOT a string like 'high'.\n"
        "Rules:\n"
        + lang_rule + "\n"
        "- suggested_title must describe the WHOLE document, not one subsection.\n"
        "- suggested_outline must be 3 to 8 short slide/section headings.\n"
        "- Keep headings presentation-ready and coherent.\n"
        "- Exclude citations, contact metadata, table headers, isolated numbers, decorative labels.\n"
        "- For numbered principles/checklists, group items meaningfully instead of copying full sentences.\n"
        "- Prefer topic-bearing content blocks over contact-only or metadata-only blocks.\n\n"
        f"DOCUMENT ID: {document_id}\n"
        f"SOURCE FILE: {source_file}\n"
        f"DOCUMENT REGIME: {profile.get('document_regime')}\n"
        f"PRIMARY SUBJECT: {primary_subject}\n\n"
        + body_section
        + "PAGE INSIGHTS:\n" + "\n".join(page_lines[:12]) + "\n\n"
        "MUST-HAVE POINTS:\n" + "\n".join(must_lines[:10]) + "\n\n"
        "TOP CONTENT UNITS:\n" + "\n".join(unit_lines[:12]) + "\n\n"
        "SECTION MAP:\n" + "\n".join(section_lines[:10]) + "\n"
    )


def _llm_document_insights(prompt: str) -> Dict[str, Any]:
    try:
        raw = chat(Config.LLM_MODEL_NAME, [{"role": "user", "content": prompt}], temperature=0.1, max_tokens=1200)
    except Exception:
        return {}
    text = (raw or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        data = __import__("json").loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_outline_candidate(text: str) -> str:
    clean = _outline_label(text)
    clean = re.sub(r"^\d+(?:\.\d+)*\s*", "", clean)
    if _is_generic_outline_heading(clean):
        return ""
    return clean[:120]


def _body_text_sample(markdown: str, max_chars: int = 1200) -> str:
    lines = []
    total = 0
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--") or stripped.startswith("![") or stripped.startswith("|"):
            continue
        lines.append(stripped)
        total += len(stripped)
        if total >= max_chars:
            break
    return " ".join(lines)[:max_chars]


def _detect_body_language_hint(body_sample: str) -> str:
    """Return a human-readable language name by counting function-word hits."""
    padded = " " + (body_sample or "").lower() + " "
    candidates = {
        "English": [" the ", " is ", " are ", " was ", " were ", " that ", " this ", " have ", " from ", " with ", " they ", " their "],
        "Vietnamese": [" của ", " và ", " trong ", " được ", " là ", " không ", " với ", " các ", " một ", " đã ", " cho ", " khi "],
        "French": [" les ", " des ", " une ", " est ", " dans ", " avec ", " pour ", " que ", " sur ", " aux ", " ils ", " leur "],
        "Spanish": [" los ", " las ", " una ", " está ", " para ", " que ", " con ", " del ", " por ", " como ", " sus ", " ellos "],
        "German": [" der ", " die ", " das ", " ist ", " und ", " mit ", " von ", " für ", " nicht ", " auf ", " sie ", " haben "],
        "Indonesian": [" yang ", " dan ", " di ", " ke ", " dari ", " ini ", " dengan ", " pada ", " untuk ", " itu ", " atau ", " juga "],
        "Tagalog": [" ang ", " mga ", " nang ", " siya ", " niya ", " kami ", " kayo ", " sila ", " namin ", " kanila "],
    }
    scores = {lang: sum(padded.count(m) for m in markers) for lang, markers in candidates.items()}
    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    return best_lang if best_score >= 3 else ""


def _document_summary(page_cards: List[Dict[str, Any]], page_insights: List[Dict[str, Any]]) -> str:
    pieces = []
    insight_by_page = {item["page"]: item for item in page_insights}
    for card in page_cards[:12]:
        page = card.get("page")
        insight = insight_by_page.get(page, {})
        insight_line = ""
        if insight.get("must_have_points"):
            insight_line = " | must-have: " + "; ".join(insight["must_have_points"][:3])
        pieces.append(f"Page {page}: {card.get('summary', '')}{insight_line}")
    return "\n".join(pieces)[:5000]


def _asset_manifest(page_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets = []
    for card in page_cards:
        for asset in card.get("assets", []):
            assets.append({"page": card.get("page"), "description": asset})
    return assets


def _must_have_prompt(
    document_id: str,
    source_file: str,
    profile: Dict[str, Any],
    page_insights: List[Dict[str, Any]],
    section_map: List[Dict[str, Any]],
    document_language: str,
) -> str:
    insight_lines = []
    for item in page_insights[:10]:
        must = "; ".join(item.get("must_have_points", [])[:4])
        support = "; ".join(item.get("support_points", [])[:3])
        insight_lines.append(
            f"- p.{item.get('page')} [{item.get('page_role')}] {item.get('page_title')}: must-have=({must}) support=({support})"
        )
    section_lines = [f"- p.{item.get('page')} {item.get('title')}" for item in section_map[:12]]
    dense_section_lines = [line for line in section_lines if len(line.split()) >= 4]
    return (
        "You are selecting the core presentation points that a slide deck MUST include.\n"
        "Return ONLY JSON array. Each item must be an object with keys: label, summary.\n"
        "Pick 4 to 8 high-value points for a presentation. Focus on what matters most, not every heading.\n"
        "Avoid citation metadata, contact information, URLs, isolated numbers, file sizes, table headers, and decorative text.\n"
        f"Same language as the source. Expected language code: {document_language}.\n\n"
        f"DOCUMENT ID: {document_id}\n"
        f"SOURCE FILE: {source_file}\n"
        f"DOCUMENT REGIME: {profile.get('document_regime')}\n\n"
        "PAGE INSIGHTS:\n"
        + "\n".join(insight_lines[:12])
        + "\n\nSECTION MAP:\n"
        + "\n".join(dense_section_lines[:12] or section_lines[:12])
    )


def _llm_must_have_points(prompt: str) -> List[Dict[str, str]]:
    try:
        raw = chat(Config.LLM_MODEL_NAME, [{"role": "user", "content": prompt}], temperature=0.1, max_tokens=1200)
    except Exception:
        return []
    text = (raw or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        data = __import__("json").loads(text)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    points: List[Dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        label = _squash(item.get("label", ""))[:140]
        summary = _squash(item.get("summary", ""))[:240]
        if not label:
            continue
        points.append({"label": label, "summary": summary or label})
    return points[:8]


def _match_suggestion_to_units(suggestion: Dict[str, str], content_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    query = f"{suggestion.get('label', '')} {suggestion.get('summary', '')}".lower()
    query_terms = [term for term in _WORD_RE.findall(query) if len(term) >= 4 and term not in _STOPWORDS]
    scored = []
    for unit in content_units:
        hay = f"{unit.get('title', '')} {unit.get('summary', '')} {unit.get('outline_label', '')}".lower()
        matched_terms = {term for term in query_terms if term.lower() in hay}
        if query_terms and len(matched_terms) / max(1, min(len(query_terms), 8)) < 0.18:
            continue
        score = len(matched_terms) * 3
        if unit.get("type") in {"section", "table_row", "numbered_item", "page_focus", "detail_block", "detail_bullet", "detail_row"}:
            score += 1
        score += float(unit.get("salience_score", 0.0)) * 2
        score += _evidence_richness_bonus(unit) * 3
        if score > 0:
            scored.append((score, unit))
    scored.sort(key=lambda item: (-item[0], _first_source_page(item[1]), item[1].get("title", "")))
    return [unit for _, unit in scored[:3]]


def _fallback_must_have_points(content_units: List[Dict[str, Any]], page_insights: List[Dict[str, Any]], regime: str) -> List[Dict[str, Any]]:
    if regime == "numbered_principles_document":
        numbered = sorted(
            [unit for unit in content_units if unit.get("type") == "numbered_item" and unit.get("number") is not None],
            key=lambda item: int(item.get("number") or 0),
        )
        selected = []
        for unit in numbered[:10]:
            selected.append({
                "point_id": f"mh{len(selected) + 1:02d}",
                "label": str(unit["number"]),
                "summary": unit.get("summary"),
                "source_unit_ids": [unit.get("unit_id")],
                "source_pages": unit.get("source_pages", []),
                "salience_score": round(float(unit.get("salience_score", 0.0)) + 0.4, 3),
                "number": unit.get("number"),
            })
        if selected:
            return selected
    ranked = []
    for unit in content_units:
        if unit.get("quality") == "noise":
            continue
        score = float(unit.get("salience_score", 0.0))
        score += _evidence_richness_bonus(unit) * 2
        score += _page_insight_bonus(unit, page_insights)
        if regime == "table_heavy_document" and unit.get("type") == "table_row":
            score += 0.3
        if regime == "table_heavy_document" and unit.get("type") != "table_row":
            score -= 0.2
        if regime == "numbered_principles_document" and unit.get("type") == "numbered_item":
            score += 0.45
        if regime == "numbered_principles_document" and unit.get("type") in {"page_focus", "must_have_hint"}:
            score -= 0.25
        ranked.append((score, unit))
    ranked.sort(key=lambda item: (-item[0], _first_source_page(item[1]), item[1].get("title", "")))
    selected = []
    seen_merge = set()
    for score, unit in ranked:
        merge_key = unit.get("merge_key") or unit.get("outline_label") or unit.get("title")
        if merge_key in seen_merge:
            continue
        seen_merge.add(merge_key)
        selected.append({
            "point_id": f"mh{len(selected) + 1:02d}",
            "label": _must_have_label(unit, regime),
            "summary": unit.get("summary"),
            "source_unit_ids": [unit.get("unit_id")],
            "source_pages": unit.get("source_pages", []),
            "salience_score": round(score, 3),
            "number": unit.get("number"),
        })
        if len(selected) >= 8:
            break
    selected = _ensure_evidence_rich_coverage(selected, content_units)
    return selected


def _must_have_label(unit: Dict[str, Any], regime: str) -> str:
    if regime == "numbered_principles_document" and unit.get("number") is not None:
        return str(unit["number"])
    raw = unit.get("outline_label") or unit.get("title") or unit.get("summary", "")[:120]
    return _squash(_strip_md_images(raw))


def _ensure_evidence_rich_coverage(selected: List[Dict[str, Any]], content_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(selected) >= 6:
        return selected
    selected_ids = {unit_id for item in selected for unit_id in item.get("source_unit_ids", [])}
    rich_units = [
        unit for unit in content_units
        if unit.get("unit_id") not in selected_ids and _evidence_rich_bonus_for_selection(unit) >= 0.28
    ]
    rich_units.sort(
        key=lambda unit: (
            -(_evidence_rich_bonus_for_selection(unit) + float(unit.get("salience_score", 0.0))),
            _first_source_page(unit),
            unit.get("title", ""),
        )
    )
    if not rich_units:
        return selected
    existing_rich = sum(1 for item in selected if any(_evidence_rich_bonus_for_selection(unit) >= 0.28 for unit in content_units if unit.get("unit_id") in item.get("source_unit_ids", [])))
    if existing_rich >= 2:
        return selected
    for unit in rich_units[:2]:
        selected.append({
            "point_id": f"mh{len(selected) + 1:02d}",
            "label": _must_have_label(unit, "sectioned_document"),
            "summary": unit.get("summary"),
            "source_unit_ids": [unit.get("unit_id")],
            "source_pages": unit.get("source_pages", []),
            "salience_score": round(float(unit.get("salience_score", 0.0)) + _evidence_rich_bonus_for_selection(unit), 3),
            "number": unit.get("number"),
        })
        if len(selected) >= 8:
            break
    return selected


def _augment_diverse_points(selected: List[Dict[str, Any]], content_units: List[Dict[str, Any]], target_count: int = 6) -> List[Dict[str, Any]]:
    existing_ids = {unit_id for item in selected for unit_id in item.get("source_unit_ids", [])}
    existing_keys = set()
    for item in selected:
        for unit in content_units:
            if unit.get("unit_id") in item.get("source_unit_ids", []):
                existing_keys.add(unit.get("merge_key") or unit.get("outline_label") or unit.get("title"))
    candidates = []
    for unit in content_units:
        unit_id = unit.get("unit_id")
        merge_key = unit.get("merge_key") or unit.get("outline_label") or unit.get("title")
        if not unit_id or unit_id in existing_ids:
            continue
        if merge_key in existing_keys:
            continue
        if unit.get("quality") == "noise" or _looks_noise_unit_for_prompt(unit):
            continue
        score = float(unit.get("salience_score", 0.0)) + _evidence_richness_bonus(unit) * 2.5
        if unit.get("type") in {"detail_block", "detail_bullet", "detail_row"}:
            score += 0.18
        candidates.append((score, unit))
    candidates.sort(key=lambda item: (-item[0], _first_source_page(item[1]), item[1].get("title", "")))
    enriched = list(selected)
    for score, unit in candidates:
        enriched.append({
            "point_id": f"mh{len(enriched) + 1:02d}",
            "label": _must_have_label(unit, "sectioned_document"),
            "summary": unit.get("summary"),
            "source_unit_ids": [unit.get("unit_id")],
            "source_pages": unit.get("source_pages", []),
            "salience_score": round(score, 3),
            "number": unit.get("number"),
        })
        existing_keys.add(unit.get("merge_key") or unit.get("outline_label") or unit.get("title"))
        if len(enriched) >= target_count:
            break
    return enriched


def _looks_noise_unit_for_prompt(unit: Dict[str, Any]) -> bool:
    text = f"{unit.get('title', '')} {unit.get('summary', '')}".lower()
    if unit.get("quality") == "noise":
        return True
    if unit.get("type") == "page_focus":
        return True
    if _identity_noise_penalty(unit) >= 0.22:
        return True
    return any(term in text for term in ["email", "linkedin", "github", "bio.link", "địa chỉ", "số điện thoại"])


def _evidence_rich_bonus_for_selection(unit: Dict[str, Any]) -> float:
    return _evidence_richness_bonus(unit) - _identity_noise_penalty(unit)


def _page_insight_bonus(unit: Dict[str, Any], page_insights: List[Dict[str, Any]]) -> float:
    page = _first_source_page(unit)
    insight = next((item for item in page_insights if item.get("page") == page), None)
    if not insight:
        return 0.0
    hay = f"{unit.get('title', '')} {unit.get('summary', '')}".lower()
    bonus = 0.0
    for item in insight.get("must_have_points", []):
        for term in _WORD_RE.findall(item.lower()):
            if term in hay:
                bonus += 0.08
    for item in insight.get("noise_points", []):
        for term in _WORD_RE.findall(item.lower()):
            if term in hay:
                bonus -= 0.08
    return bonus


def _extract_numbered_items(page_md: str) -> List[Dict[str, Any]]:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", page_md)
    text = re.sub(r"\*(?:Figure|Table|Fig\.?|Bảng|Hình)[:\s]+[^*]+\*", " ", text, flags=re.IGNORECASE)
    pattern = re.compile(r"(?ms)^\s*(\d{1,2})[.)]\s+(.+?)(?=^\s*\d{1,2}[.)]\s+|\n\s*!\[|\n\s*---|\Z)")
    items = []
    for number, body in pattern.findall(text):
        clean = _squash(body)
        if len(clean) < 16 or _is_noise_text(clean) or _looks_like_citation_text(clean):
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


def _extract_markdown_tables(page_md: str) -> List[str]:
    lines = page_md.splitlines()
    tables: List[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"^\s*\|.+\|\s*$", lines[i]):
            chunk = [lines[i]]
            j = i + 1
            while j < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[j]):
                chunk.append(lines[j])
                j += 1
            if len(chunk) >= 2 and re.match(r"^\s*\|[-:\s|]+\|\s*$", chunk[1]):
                tables.append("\n".join(chunk))
            i = j
            continue
        i += 1
    return tables


def _table_row_units(table_md: str) -> List[Tuple[str, str]]:
    lines = [line.strip() for line in table_md.splitlines() if line.strip()]
    if len(lines) < 3:
        return []
    rows = []
    header = [_squash(cell) for cell in lines[0].strip("|").split("|")]
    for row_line in lines[2:]:
        cells = [_squash(cell) for cell in row_line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        title_idx = _best_table_title_index(cells)
        title = cells[title_idx]
        summary_parts = [cell for idx, cell in enumerate(cells) if idx != title_idx and cell]
        if header and len(header) == len(cells):
            summary = "; ".join(f"{header[idx]}: {cell}" for idx, cell in enumerate(cells) if idx != title_idx and cell)
        else:
            summary = "; ".join(summary_parts)
        rows.append((title, summary))
    return rows


def _best_table_title_index(cells: List[str]) -> int:
    scored = []
    for idx, cell in enumerate(cells):
        score = 0.0
        words = cell.split()
        if len(cell) >= 12:
            score += 1.5
        if 2 <= len(words) <= 14:
            score += 1.0
        if _looks_like_data_cell_title(cell):
            score -= 2.5
        if _EMAIL_RE.search(cell) or _URL_RE.search(cell):
            score -= 2.0
        score -= idx * 0.15
        scored.append((score, idx))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1] if scored else 0


def _base_salience(unit: Dict[str, Any], page_insights: List[Dict[str, Any]]) -> float:
    score = 0.2
    if unit.get("type") == "section":
        score += 0.22
    if unit.get("type") == "numbered_item":
        score += 0.24
    if unit.get("type") == "table_row":
        score += 0.18
    if unit.get("type") in {"detail_block", "detail_bullet", "detail_row"}:
        score += 0.2
    if unit.get("quality") == "core":
        score += 0.16
    summary = unit.get("summary", "")
    if len(summary) >= 80:
        score += 0.12
    if len(summary) >= 180:
        score += 0.08
    if unit.get("outline_label"):
        score += 0.08
    score += _evidence_richness_bonus(unit)
    score -= _identity_noise_penalty(unit)
    score += _page_insight_bonus(unit, page_insights)
    return round(max(0.0, min(score, 1.5)), 3)


def _make_unit(
    counter: int,
    unit_type: str,
    title: str,
    summary: str,
    source_pages: List[int],
    quality: str,
    outline_label: str = "",
    number: int | None = None,
) -> Dict[str, Any]:
    return {
        "unit_id": f"u{counter:03d}_{unit_type}_p{source_pages[0] if source_pages else 0}",
        "type": unit_type,
        "title": _squash(title)[:180],
        "summary": _squash(summary)[:420],
        "source_pages": source_pages,
        "quality": quality,
        "number": number,
        "outline_label": outline_label or _outline_label(title),
        "merge_key": _merge_key(title, summary),
    }


def _merge_key(title: str, summary: str) -> str:
    base = _outline_label(title) or _outline_label(summary)
    return base.lower()


def _outline_label(text: str) -> str:
    clean = _squash(_strip_md_images(text))
    clean = re.sub(r"[*_`#]+", "", clean)
    clean = re.sub(r"^\d+(?:\.\d+)*[.)]?\s*", "", clean)
    clean = re.sub(r"\s*[:;,-]\s*$", "", clean)
    if _is_noise_text(clean):
        return ""
    words = clean.split()
    if len(words) > 20:
        words = words[:20]
        while len(words) > 4 and words[-1].lower() in _TRAILING_TRIM_WORDS:
            words.pop()
        clean = " ".join(words)
    return clean[:120]


def _is_generic_outline_heading(text: str) -> bool:
    lower = _squash(text).lower()
    if not lower:
        return True
    generic = {
        "additional information",
        "other information",
        "more information",
        "miscellaneous",
        "general information",
        "thông tin thêm",
        "thông tin khác",
        "khác",
        "ghi chú",
    }
    return lower in generic


def _is_generic_subject(text: str) -> bool:
    lower = _squash(text).lower()
    return lower in {
        "introduction",
        "overview",
        "summary",
        "background",
        "abstract",
        "methodology",
        "conclusion",
        "references",
        "contents",
        "table of contents",
        "mục tiêu nghề nghiệp",
        "học vấn",
        "kỹ năng",
    }


def _looks_like_data_cell_title(text: str) -> bool:
    clean = _squash(text)
    if not clean:
        return True
    if _SIZE_ONLY_RE.match(clean):
        return True
    if re.fullmatch(r"[\d.]+%?", clean):
        return True
    if re.fullmatch(r"[A-Z]{1,4}\d*", clean):
        return True
    if len(clean.split()) <= 2 and re.search(r"\d", clean):
        return True
    return False


def _looks_supportish(title: str, summary: str) -> bool:
    text = f"{title} {summary}".lower()
    if _EMAIL_RE.search(text) or _URL_RE.search(text):
        return True
    if any(term in text for term in ["phone", "email", "github", "linkedin", "figma", "contact"]):
        return True
    return False


def _evidence_richness_bonus(unit: Dict[str, Any]) -> float:
    text = f"{unit.get('title', '')} {unit.get('summary', '')}"
    score = 0.0
    if re.search(r"\b(?:19|20)\d{2}\b", text):
        score += 0.1
    if re.search(r"\b(?:html|css|flutter|java|javafx|asp\.net|c#|sql|mysql|figma|firestore|python|react|vue|node)\b", text, flags=re.IGNORECASE):
        score += 0.16
    if re.search(r"\b(phát triển|thiết kế|xây dựng|triển khai|phân tích|lập trình|developed|designed|implemented|built|created|managed|analysed|analyzed)\b", text, flags=re.IGNORECASE):
        score += 0.16
    if re.search(r"\b(vị trí|vai trò|position|role|responsibility|responsibilities)\b", text, flags=re.IGNORECASE):
        score += 0.12
    if re.search(r"\b(project|dự án|ứng dụng|application|system|prototype|workflow|platform)\b", text, flags=re.IGNORECASE):
        score += 0.1
    return min(score, 0.42)


def _identity_noise_penalty(unit: Dict[str, Any]) -> float:
    text = f"{unit.get('title', '')} {unit.get('summary', '')}".lower()
    penalty = 0.0
    if unit.get("type") == "page_focus":
        penalty += 0.12
    if any(term in text for term in ["thông tin liên hệ", "contact", "linkedin", "github", "email", "địa chỉ", "số điện thoại", "phone"]):
        penalty += 0.22
    if "figure:" in text and len(text.split()) < 20:
        penalty += 0.18
    return min(penalty, 0.35)


def _is_metadata_noise(text: str) -> bool:
    clean = _squash(text).lower()
    if not clean:
        return True
    tokens = clean.split()
    contact_hits = 0
    if _EMAIL_RE.search(clean):
        contact_hits += 2
    if _URL_RE.search(clean):
        contact_hits += 2
    for term in ("phone", "email", "linkedin", "github", "address", "tel", "contact"):
        if term in clean:
            contact_hits += 1
    return len(tokens) <= 24 and contact_hits >= 3


def _is_noise_text(text: str) -> bool:
    clean = _squash(text)
    if not clean:
        return True
    lower = clean.lower()
    if any(lower.startswith(prefix) for prefix in _NOISE_PREFIXES):
        return True
    if _SIZE_ONLY_RE.match(clean):
        return True
    if _URL_RE.search(clean) and len(clean.split()) <= 14:
        return True
    if _EMAIL_RE.search(clean) and len(clean.split()) <= 18:
        return True
    if re.match(r"^page\s+\d+", lower):
        return True
    if re.match(r"^\|.*\|$", clean):
        return True
    if clean.count("|") >= 2:
        return True
    if _looks_like_citation_text(clean):
        return True
    if len(clean) <= 4 and clean.isupper():
        return True
    if bool(re.search(r"\bvol\.?\s*\d+\b", lower) and re.search(r"\b\d{4}\b", lower)):
        return True
    return False


def _looks_like_citation_text(text: str) -> bool:
    clean = _squash(text)
    lower = clean.lower()
    if not clean:
        return False
    if "doi:" in lower or "doi.org" in lower:
        return True
    has_year = bool(re.search(r"\b(?:19|20)\d{2}\b", clean))
    citation_markers = sum(1 for marker in [" et al", "proceedings", "journal", "conference", "vol.", "doi", "acm", "ieee", "springer", "nature", "science"] if marker in lower)
    punctuation_density = clean.count(",") + clean.count("(") + clean.count(")")
    authorish_start = bool(re.match(r"^[A-Z][A-Za-zÀ-ỹ'’-]+,\s+[A-Z]", clean))
    if has_year and authorish_start and (punctuation_density >= 4 or citation_markers >= 1):
        return True
    if has_year and citation_markers >= 2 and punctuation_density >= 3:
        return True
    return False


def _first_source_page(item: Dict[str, Any]) -> int:
    pages = item.get("source_pages", []) if isinstance(item, dict) else []
    if not pages:
        return 999
    return min(int(page) for page in pages)


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


def _squash(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _is_structural_heading_only(text: str) -> bool:
    return bool(_STRUCTURAL_HEADING_RE.match(_squash(text)))
