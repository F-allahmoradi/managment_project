"""پارسر فکت از پاسخ مدل؛ حساب و شاهد در derive بررسی می‌شود."""

from typing import Any

from business_logic.config import load_column_config
from business_logic.derive import filter_facts, parse_number
from business_logic.normalizer import clean_text, find_span
from business_logic.validator import (
    accept_confidence,
    accept_derivation,
    accept_grounding,
    accept_kind,
    accept_role,
    accept_unit,
)
from schemas.output import FactHit

_SOURCE_KEY = "project_texts"


def _string_list(raw: Any) -> list[str]:
    """لیست رشته را تمیز می‌کند."""
    if isinstance(raw, str) and raw.strip():
        return [clean_text(raw)]
    if not isinstance(raw, list):
        return []
    items: list[str] = []
    for value in raw:
        text = clean_text(str(value or ""))
        if text:
            items.append(text)
    return items


def _id_list(raw: Any) -> list[str]:
    """شناسه منابع را می‌خواند."""
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if not isinstance(raw, list):
        return []
    items: list[str] = []
    for value in raw:
        text = str(value or "").strip()
        if text:
            items.append(text)
    return items


def _span_or_empty(normalized: str, fragment: str) -> tuple[str, int, int]:
    """شاهد را اگر در متن باشد با آفست برمی‌گرداند."""
    mention = clean_text(fragment)
    if not mention:
        return "", -1, -1
    span = find_span(normalized, mention)
    if span is None:
        return mention, -1, -1
    start, end = span
    return normalized[start:end], start, end


def _coerce_fact(item: Any, index: int, normalized: str) -> FactHit | None:
    """یک آیتم مدل را اگر نوعش مجاز باشد به فکت تبدیل می‌کند."""
    if not isinstance(item, dict):
        return None
    kind = accept_kind(item.get("kind") or item.get("type"))
    grounding = accept_grounding(item.get("grounding") or item.get("explicitness"))
    if kind is None or grounding is None:
        return None
    name = clean_text(str(item.get("name") or item.get("label") or kind["name"]))
    if not name:
        return None
    mention, start, end = _span_or_empty(
        normalized,
        str(item.get("mention_text") or item.get("evidence") or ""),
    )
    unit_meta = accept_unit(item.get("unit"))
    role = accept_role(item.get("role"))
    derivation = accept_derivation(item.get("derivation"))
    fact_id = str(item.get("id") or item.get("fact_id") or f"f{index + 1}").strip()
    evidence = _string_list(item.get("evidence_texts") or item.get("evidence"))
    evidence = [part for part in evidence if find_span(normalized, part) is not None]
    if (
        mention
        and mention not in evidence
        and find_span(normalized, mention) is not None
    ):
        evidence.insert(0, mention)
    return FactHit(
        fact_id=fact_id,
        kind=str(kind["code"]),
        kind_name=str(kind["name"]),
        name=name,
        value=parse_number(item.get("value")),
        unit=None if unit_meta is None else str(unit_meta["code"]),
        unit_name=None if unit_meta is None else str(unit_meta["name"]),
        role=str(role["code"]),
        effect=clean_text(str(item.get("effect") or "")),
        previous=clean_text(str(item.get("previous") or item.get("from") or "")),
        current=clean_text(str(item.get("current") or item.get("to") or "")),
        grounding=str(grounding["code"]),
        grounding_name=str(grounding["name"]),
        derivation="" if derivation is None else str(derivation["code"]),
        source_ids=_id_list(item.get("source_ids") or item.get("sources")),
        mention_text=mention,
        start_offset=start,
        end_offset=end,
        evidence_texts=evidence,
        confidence=accept_confidence(item.get("confidence")),
    )


def facts_from_payload(payload: Any, normalized: str) -> tuple[list[FactHit], int]:
    """فکت‌های مجاز را از پاسخ مدل برمی‌دارد و بی‌شاهدها را حذف می‌کند."""
    if not isinstance(payload, dict):
        return [], 0
    raw = payload.get("facts")
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return [], 0
    max_hits = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("facts") or {}).get(
            "max"
        )
        or 24
    )
    hits: list[FactHit] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        fact = _coerce_fact(item, index, normalized)
        if fact is None or fact.fact_id in seen:
            continue
        seen.add(fact.fact_id)
        hits.append(fact)
        if len(hits) >= max_hits:
            break
    return filter_facts(hits, normalized)
