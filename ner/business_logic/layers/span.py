"""لایه span: ذکر موجودیت و کلمهٔ کلیدی.

جدول هدف: entity_mentions / entities. OBJECT اینجاست نه در موضوع.
"""

from typing import Any

from business_logic.config import load_column_config
from business_logic.normalizer import clean_text, find_span, normalize_name
from business_logic.time_parse import parse_occurred_at
from business_logic.validator import accept_confidence, accept_entity_type
from schemas.output import CanonicalEntityHit, EntityMentionHit, KeywordHit

_SOURCE_KEY = "project_texts"


def _coerce_mention(item: Any) -> dict | None:
    """یک آیتم mentions مدل را به دیکشنری تخت تبدیل می‌کند."""
    if not isinstance(item, dict):
        return None
    entity_type = accept_entity_type(item.get("type") or item.get("entity_type"))
    if entity_type is None:
        return None
    canonical = clean_text(str(item.get("canonical_name") or item.get("value") or ""))
    mention = clean_text(str(item.get("mention_text") or item.get("evidence") or canonical))
    if not canonical or not mention:
        return None
    return {
        "type": entity_type,
        "canonical_name": canonical,
        "mention_text": mention,
        "confidence": accept_confidence(item.get("confidence")),
        "occurred_at_raw": item.get("occurred_at"),
    }


def mentions_from_payload(payload: Any, normalized: str) -> list[EntityMentionHit]:
    """پاسخ مدل را به ذکرهای با آفست معتبر تبدیل می‌کند."""
    if not isinstance(payload, dict):
        return []
    raw_items = payload.get("mentions")
    if raw_items is None:
        raw_items = payload.get("entities")
    if not isinstance(raw_items, list):
        return []
    max_mentions = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("mentions") or {}).get(
            "max"
        )
        or 80
    )
    hits: list[EntityMentionHit] = []
    seen: set[tuple[str, int, int]] = set()
    for item in raw_items:
        coerced = _coerce_mention(item)
        if coerced is None:
            continue
        span = find_span(normalized, coerced["mention_text"])
        if span is None:
            span = find_span(normalized, coerced["canonical_name"])
        if span is None:
            continue
        start, end = span
        coerced["mention_text"] = normalized[start:end]
        key = (coerced["type"], start, end)
        if key in seen:
            continue
        seen.add(key)
        occurred_at = None
        if coerced["type"] == "TIME":
            occurred_at = parse_occurred_at(
                coerced["mention_text"],
                coerced["canonical_name"],
                coerced.get("occurred_at_raw"),
            )
        hits.append(
            EntityMentionHit(
                type=coerced["type"],
                canonical_name=coerced["canonical_name"],
                normalized_name=normalize_name(coerced["canonical_name"]),
                mention_text=coerced["mention_text"],
                start_offset=start,
                end_offset=end,
                confidence=coerced["confidence"],
                occurred_at=occurred_at,
            )
        )
        if len(hits) >= max_mentions:
            break
    hits.sort(key=lambda item: (item.start_offset, item.end_offset, item.type))
    return hits


def keywords_from_payload(payload: Any, normalized: str) -> list[KeywordHit]:
    """عبارت‌های کلیدی آزاد را اگر در متن باشند نگه می‌دارد."""
    if not isinstance(payload, dict) or not isinstance(payload.get("keywords"), list):
        return []
    max_keywords = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("keywords") or {}).get(
            "max"
        )
        or 12
    )
    hits: list[KeywordHit] = []
    seen: set[str] = set()
    for item in payload["keywords"]:
        if not isinstance(item, dict):
            continue
        phrase = normalize_name(str(item.get("phrase") or item.get("value") or ""))
        mention = clean_text(str(item.get("mention_text") or item.get("evidence") or phrase))
        if not phrase or phrase in seen:
            continue
        span = find_span(normalized, mention)
        if span is None:
            span = find_span(normalized, phrase)
        if span is None:
            continue
        start, end = span
        seen.add(phrase)
        hits.append(
            KeywordHit(
                phrase=phrase,
                mention_text=normalized[start:end],
                start_offset=start,
                end_offset=end,
                confidence=accept_confidence(item.get("confidence")),
            )
        )
        if len(hits) >= max_keywords:
            break
    hits.sort(key=lambda item: (-item.confidence, item.start_offset))
    return hits


def drop_entity_copy_keywords(
    keywords: list[KeywordHit],
    mentions: list[EntityMentionHit],
) -> list[KeywordHit]:
    """عبارتی که همان ذکر موجودیت است کلمهٔ کلیدی جدا حساب نمی‌شود."""
    names = set()
    for mention in mentions:
        names.add(mention.normalized_name)
        names.add(normalize_name(mention.mention_text))
        names.add(normalize_name(mention.canonical_name))
    return [item for item in keywords if item.phrase not in names]


def canonical_from_mentions(mentions: list[EntityMentionHit]) -> list[CanonicalEntityHit]:
    """ذکرهای هم‌نوع و هم‌نام را به موجودیت canonical جمع می‌کند."""
    grouped: dict[tuple[str, str], CanonicalEntityHit] = {}
    for mention in mentions:
        key = (mention.type, mention.normalized_name)
        current = grouped.get(key)
        if current is None:
            grouped[key] = CanonicalEntityHit(
                type=mention.type,
                canonical_name=mention.canonical_name,
                normalized_name=mention.normalized_name,
                mention_count=1,
            )
        else:
            current.mention_count += 1
    return list(grouped.values())
