"""لایه stance: قطبیت کل متن و هیجان.

جدول هدف: text_analysis_sentiments (یکی) و text_analysis_emotions (چندتا).
با موضوع و موجودیت قاطی نمی‌شود.
"""

from typing import Any

from business_logic.config import load_column_config, load_stance_catalog
from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence
from schemas.output import EmotionHit, SentimentHit

_SOURCE_KEY = "project_texts"


def _index_by_code(rows: list[dict]) -> dict[str, dict]:
    """lookup کد را می‌سازد."""
    return {str(item["code"]): item for item in rows}


def _lookup(value: Any, catalog: dict[str, dict]) -> dict | None:
    """کد را اگر در کاتالوگ باشد برمی‌گرداند."""
    if not isinstance(value, str):
        return None
    code = value.strip().lower()
    return catalog.get(code)


def _evidence(normalized: str, item: dict, fallback: str = "") -> str:
    """شاهد را اگر در متن باشد برمی‌دارد."""
    mention = clean_text(str(item.get("mention_text") or item.get("evidence") or fallback))
    if not mention:
        return ""
    span = find_span(normalized, mention)
    if span is None:
        return mention
    return normalized[span[0] : span[1]]


def _intensity(raw: Any, intensities: dict[str, dict]) -> dict:
    """شدت را اگر نامعتبر بود متوسط می‌گذارد."""
    found = _lookup(raw, intensities)
    if found is not None:
        return found
    return intensities.get("medium") or next(iter(intensities.values()))


def sentiment_from_payload(payload: Any, normalized: str) -> SentimentHit | None:
    """قطبیت کل متن را اگر کد مجاز باشد برمی‌گرداند."""
    if not isinstance(payload, dict):
        return None
    raw = payload.get("sentiment")
    if isinstance(raw, list) and raw:
        raw = raw[0]
    if not isinstance(raw, dict):
        return None
    catalog = load_stance_catalog()
    polarities = _index_by_code(catalog["polarities"])
    intensities = _index_by_code(catalog["intensity_levels"])
    polarity = _lookup(raw.get("polarity") or raw.get("code"), polarities)
    if polarity is None:
        return None
    intensity = _intensity(raw.get("intensity"), intensities)
    return SentimentHit(
        polarity=str(polarity["code"]),
        polarity_name=str(polarity["name"]),
        intensity=str(intensity["code"]),
        intensity_name=str(intensity["name"]),
        intensity_level=int(intensity["level"]),
        mention_text=_evidence(normalized, raw),
        confidence=accept_confidence(raw.get("confidence")),
    )


def emotions_from_payload(payload: Any, normalized: str) -> list[EmotionHit]:
    """هیجان‌های مجاز را از پاسخ مدل برمی‌دارد."""
    if not isinstance(payload, dict) or not isinstance(payload.get("emotions"), list):
        return []
    catalog = load_stance_catalog()
    emotions = _index_by_code(catalog["emotions"])
    intensities = _index_by_code(catalog["intensity_levels"])
    max_emotions = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("emotions") or {}).get(
            "max"
        )
        or 3
    )
    hits: list[EmotionHit] = []
    seen: set[str] = set()
    for item in payload["emotions"]:
        if not isinstance(item, dict):
            continue
        meta = _lookup(item.get("emotion") or item.get("code"), emotions)
        if meta is None or meta["code"] in seen:
            continue
        intensity = _intensity(item.get("intensity"), intensities)
        seen.add(str(meta["code"]))
        hits.append(
            EmotionHit(
                emotion=str(meta["code"]),
                name=str(meta["name"]),
                intensity=str(intensity["code"]),
                intensity_name=str(intensity["name"]),
                intensity_level=int(intensity["level"]),
                mention_text=_evidence(normalized, item, str(meta["name"])),
                confidence=accept_confidence(item.get("confidence")),
            )
        )
        if len(hits) >= max_emotions:
            break
    hits.sort(key=lambda item: (-item.intensity_level, -item.confidence))
    return hits
