"""پارسر نقل‌قول؛ گوینده و محتوا باید در متن باشند."""

from typing import Any

from business_logic.config import load_column_config
from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence, accept_quote_mode
from schemas.output import QuoteHit

_SOURCE_KEY = "project_texts"


def _span(normalized: str, fragment: str) -> tuple[str, int, int] | None:
    """تکه را فقط اگر در متن باشد برمی‌گرداند."""
    mention = clean_text(fragment)
    if not mention:
        return None
    found = find_span(normalized, mention)
    if found is None:
        return None
    start, end = found
    return normalized[start:end], start, end


def quotes_from_payload(payload: Any, normalized: str) -> list[QuoteHit]:
    """نقل‌قول‌های دارای شاهد را نگه می‌دارد."""
    if not isinstance(payload, dict):
        return []
    raw = payload.get("quotes")
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    max_hits = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("quotes") or {}).get(
            "max"
        )
        or 8
    )
    hits: list[QuoteHit] = []
    seen: set[tuple[str, str, str]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        mode = accept_quote_mode(item.get("mode") or item.get("type"))
        speaker = _span(
            normalized,
            str(item.get("attributed_to") or item.get("speaker") or ""),
        )
        quoted = _span(
            normalized,
            str(item.get("quoted_text") or item.get("content") or ""),
        )
        cue = _span(
            normalized,
            str(item.get("mention_text") or item.get("cue") or ""),
        )
        if mode is None or speaker is None or quoted is None:
            continue
        key = (mode["code"], speaker[0], quoted[0])
        if key in seen:
            continue
        seen.add(key)
        mention = "" if cue is None else cue[0]
        start = -1 if cue is None else cue[1]
        end = -1 if cue is None else cue[2]
        if cue is None:
            mention, start, end = speaker
        hits.append(
            QuoteHit(
                mode=str(mode["code"]),
                mode_name=str(mode["name"]),
                attributed_to=speaker[0],
                quoted_text=quoted[0],
                mention_text=mention,
                start_offset=start,
                end_offset=end,
                confidence=accept_confidence(item.get("confidence")),
            )
        )
        if len(hits) >= max_hits:
            break
    return hits
