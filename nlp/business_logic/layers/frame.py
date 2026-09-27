"""پارسر قاب مسئله؛ واحد و درباره باید در متن باشند."""

from typing import Any

from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence, accept_process, accept_scope
from schemas.output import IssueFrameHit


def _in_text(normalized: str, fragment: str) -> str:
    """تکه را فقط اگر در متن باشد برمی‌گرداند."""
    mention = clean_text(fragment)
    if not mention:
        return ""
    span = find_span(normalized, mention)
    if span is None:
        return ""
    return normalized[span[0] : span[1]]


def frame_from_payload(payload: Any, normalized: str) -> IssueFrameHit | None:
    """یک قاب مسئله را اگر محدوده معتبر باشد می‌سازد."""
    if not isinstance(payload, dict):
        return None
    raw = payload.get("frame") or payload.get("issue")
    if not isinstance(raw, dict):
        return None
    scope = accept_scope(raw.get("scope"))
    if scope is None:
        return None
    process = accept_process(raw.get("process"))
    title = clean_text(str(raw.get("title") or raw.get("name") or ""))
    if not title:
        return None
    unit = _in_text(normalized, str(raw.get("unit") or ""))
    about = _in_text(normalized, str(raw.get("about") or raw.get("mention_text") or ""))
    mention = about or unit
    return IssueFrameHit(
        title=title,
        unit=unit,
        process="" if process is None else str(process["code"]),
        process_name="" if process is None else str(process["name"]),
        scope=str(scope["code"]),
        scope_name=str(scope["name"]),
        about=about,
        mention_text=mention,
        confidence=accept_confidence(raw.get("confidence")),
    )
