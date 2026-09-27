"""پارسر مشترک برچسب بسته‌کاتالوگ با یک اصلی.

ژانر و نیت هر کدام کاتالوگ و جدول جدا دارند؛ منطق انتخاب اصلی یکی است.
"""

from typing import Any, Callable

from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence


def _index_catalog(catalog: list[dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    """lookup کد و نام/هم‌معنی را می‌سازد."""
    by_code: dict[str, dict] = {}
    by_alias: dict[str, dict] = {}
    for item in catalog:
        code = str(item["code"])
        by_code[code] = item
        by_code[code.lower()] = item
        for alias in item.get("aliases") or []:
            key = str(alias).strip()
            if key:
                by_alias[key] = item
                by_alias[key.lower()] = item
    return by_code, by_alias


def _resolve(value: Any, by_code: dict[str, dict], by_alias: dict[str, dict]) -> dict | None:
    """کد یا نام فارسی را به ردیف کاتالوگ می‌برد."""
    if not isinstance(value, str):
        return None
    key = value.strip()
    if not key:
        return None
    found = by_code.get(key) or by_code.get(key.lower())
    if found is not None:
        return found
    return by_alias.get(key) or by_alias.get(key.lower())


def _evidence(normalized: str, item: dict, fallback: str = "") -> str:
    """شاهد را اگر در متن باشد برمی‌دارد."""
    mention = clean_text(
        str(item.get("mention_text") or item.get("evidence") or fallback)
    )
    if not mention:
        return ""
    span = find_span(normalized, mention)
    if span is None:
        return mention
    return normalized[span[0] : span[1]]


def _slots(raw: Any) -> dict[str, str]:
    """نقش‌های پرشده را اگر رشته باشند نگه می‌دارد."""
    if not isinstance(raw, dict):
        return {}
    filled: dict[str, str] = {}
    for key, value in raw.items():
        name = str(key or "").strip()
        text = str(value or "").strip()
        if name and text:
            filled[name] = text
    return filled


def _pick_primary(hits: list, *, priority_of: Callable) -> None:
    """دقیقاً یک اصلی می‌گذارد؛ اولویت کاتالوگ بر ادعای مدل می‌چربد."""
    if not hits:
        return
    ranked = sorted(
        hits,
        key=lambda item: (priority_of(item.code), item.confidence),
        reverse=True,
    )
    winner = ranked[0]
    for item in hits:
        item.is_primary = item is winner


def labeled_hits_from_payload(
    payload: Any,
    *,
    list_key: str,
    catalog: list[dict],
    max_hits: int,
    hit_cls,
    normalized: str,
) -> list:
    """برچسب‌های مجاز یک لایه را از پاسخ مدل برمی‌دارد."""
    if not isinstance(payload, dict):
        return []
    raw = payload.get(list_key)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        singular = payload.get(list_key.rstrip("s"))
        if isinstance(singular, dict):
            raw = [singular]
        else:
            return []
    by_code, by_alias = _index_catalog(catalog)
    priority = {item["code"]: int(item["priority"]) for item in catalog}
    hits = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        meta = (
            _resolve(item.get("code"), by_code, by_alias)
            or _resolve(item.get("type"), by_code, by_alias)
            or _resolve(item.get("name"), by_code, by_alias)
        )
        if meta is None or meta["code"] in seen:
            continue
        seen.add(str(meta["code"]))
        hits.append(
            hit_cls(
                code=str(meta["code"]),
                name=str(meta["name"]),
                is_primary=bool(item.get("is_primary")),
                mention_text=_evidence(normalized, item, str(meta["name"])),
                confidence=accept_confidence(item.get("confidence")),
                slots=_slots(item.get("slots")),
            )
        )
        if len(hits) >= max_hits:
            break
    _pick_primary(hits, priority_of=lambda code: priority.get(code, 0))
    hits.sort(
        key=lambda item: (not item.is_primary, -priority.get(item.code, 0), -item.confidence)
    )
    return hits
