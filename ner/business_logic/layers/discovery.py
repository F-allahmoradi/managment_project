"""کشف ژانر نو وقتی هیچ قالب کاتالوگ از متن پر نمی‌شود.

نوع کشف‌شده حذف نمی‌شود و به زور در قالب موجود نمی‌رود.
فقط نقش و شاهدی که داخل متن باشد پذیرفته می‌شود.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import yaml

from business_logic.config import (
    discovered_discourse_path,
    load_discourse_discovery,
)
from business_logic.layers.labeled import _evidence, _index_catalog, _resolve, _slots
from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence
from schemas.output import DiscourseHit, DiscourseTypeSchema

_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,38}$")


def _in_text(normalized: str, value: str) -> str:
    """تکه را فقط اگر داخل متن باشد برمی‌گرداند."""
    mention = clean_text(value)
    if not mention:
        return ""
    span = find_span(normalized, mention)
    if span is None:
        return ""
    return normalized[span[0] : span[1]]


def _slot_entries(raw: Any) -> list[dict[str, str]]:
    """نقش‌های پیشنهادی نوع نو را یکدست می‌کند."""
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            name = item.strip()
            description = ""
        elif isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            description = str(item.get("description") or "").strip()
        else:
            continue
        if not name or name in seen:
            continue
        seen.add(name)
        entries.append({"name": name, "description": description})
    return entries


def schema_from_catalog(item: dict) -> DiscourseTypeSchema:
    """ساختار کاتالوگ را به اسکیمای خروجی تبدیل می‌کند."""
    return DiscourseTypeSchema(
        code=str(item.get("code") or ""),
        name=str(item.get("name") or ""),
        definition=str(item.get("definition") or item.get("description") or ""),
        required_slots=_slot_entries(item.get("required_slots") or []),
        optional_slots=_slot_entries(item.get("optional_slots") or []),
        contrast=[
            str(rule).strip() for rule in (item.get("contrast") or []) if str(rule).strip()
        ],
    )


def _normalize_code(raw: Any) -> str:
    """کد انگلیسی نوع نو را یکدست می‌کند."""
    text = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not _CODE_RE.fullmatch(text):
        return ""
    return text[:40]


def _raw_items(payload: Any) -> list[dict]:
    """ژانرها و بلوک discovered را در یک فهرست می‌گذارد."""
    if not isinstance(payload, dict):
        return []
    items: list[dict] = []
    for key in ("discourses", "discovered"):
        raw = payload.get(key)
        if isinstance(raw, dict):
            items.append(raw)
        elif isinstance(raw, list):
            items.extend(item for item in raw if isinstance(item, dict))
    return items


def _filled_from_text(
    normalized: str,
    slots: dict[str, str],
    *,
    require_in_text: bool,
) -> dict[str, str]:
    """فقط نقش‌هایی را نگه می‌دارد که شاهد متنی دارند."""
    filled: dict[str, str] = {}
    for name, value in slots.items():
        text = _in_text(normalized, value) if require_in_text else clean_text(value)
        if name and text:
            filled[name] = text
    return filled


def novel_discourses_from_payload(
    payload: Any,
    normalized: str,
    catalog: list[dict],
    discovery: dict,
) -> list[DiscourseHit]:
    """نوع‌های نو را اگر ساختار و شاهد داشته باشند نگه می‌دارد."""
    if not discovery.get("enabled"):
        return []
    by_code, by_alias = _index_catalog(catalog)
    reserved = set(by_code) | set(by_alias)
    min_slots = max(1, int(discovery.get("min_required_slots") or 2))
    min_confidence = float(discovery.get("min_confidence") or 0.7)
    require_in_text = bool(discovery.get("require_in_text", True))
    hits: list[DiscourseHit] = []
    seen: set[str] = set()
    for item in _raw_items(payload):
        resolved = _resolve(
            item.get("code") or item.get("type"),
            by_code,
            by_alias,
        ) or _resolve(item.get("name"), by_code, by_alias)
        if resolved is not None:
            continue
        code = _normalize_code(item.get("code") or item.get("type"))
        name = clean_text(str(item.get("name") or ""))
        definition = clean_text(
            str(item.get("definition") or item.get("description") or "")
        )
        structured = bool(item.get("discovered")) or bool(definition and name)
        if not code or code in reserved or code in seen or not name or not structured:
            continue
        mention = _in_text(normalized, _evidence(normalized, item, name))
        if require_in_text and not mention:
            continue
        if not mention:
            mention = clean_text(str(item.get("mention_text") or name))
        filled = _filled_from_text(
            normalized,
            _slots(item.get("slots")),
            require_in_text=require_in_text,
        )
        required = _slot_entries(item.get("required_slots"))
        optional = _slot_entries(item.get("optional_slots"))
        if not required:
            required = [{"name": key, "description": ""} for key in filled]
        required_names = [entry["name"] for entry in required]
        required_filled = [key for key in required_names if key in filled]
        if len(required_filled) < min_slots:
            continue
        confidence = accept_confidence(item.get("confidence"))
        if confidence < min_confidence:
            continue
        seen.add(code)
        reserved.add(code)
        schema = DiscourseTypeSchema(
            code=code,
            name=name,
            definition=definition or name,
            required_slots=required,
            optional_slots=optional,
            contrast=[
                str(rule).strip()
                for rule in (item.get("contrast") or [])
                if str(rule).strip()
            ],
        )
        hits.append(
            DiscourseHit(
                code=code,
                name=name,
                is_primary=bool(item.get("is_primary")),
                mention_text=mention,
                confidence=confidence,
                slots=filled,
                discovered=True,
                type_schema=schema,
            )
        )
    return hits


def persist_discovered_discourses(
    hits: list[DiscourseHit],
    path: Path | None = None,
) -> None:
    """نوع نو را در YAML کاتالوگ کشف‌شده می‌نویسد؛ ردیف قبلی را حذف نمی‌کند."""
    discovery = load_discourse_discovery()
    if not discovery.get("persist"):
        return
    novel = [item for item in hits if item.discovered and item.type_schema is not None]
    if not novel:
        return
    target = path or discovered_discourse_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if target.is_file():
        loaded = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        rows = loaded.get("discourses") if isinstance(loaded, dict) else None
        if isinstance(rows, list):
            existing = [row for row in rows if isinstance(row, dict) and row.get("code")]
    by_code = {str(row.get("code")): row for row in existing}
    changed = False
    for hit in novel:
        schema = hit.type_schema
        if schema is None:
            continue
        row = by_code.get(schema.code)
        payload = {
            "code": schema.code,
            "name": schema.name,
            "priority": 0,
            "discovered": True,
            "definition": schema.definition,
            "description": schema.definition,
            "required_slots": [dict(item) for item in schema.required_slots],
            "optional_slots": [dict(item) for item in schema.optional_slots],
            "contrast": list(schema.contrast),
            "aliases": [schema.name],
        }
        if row is None:
            existing.append(payload)
            by_code[schema.code] = payload
            changed = True
            continue
        if not row.get("definition") and schema.definition:
            row["definition"] = schema.definition
            row["description"] = schema.definition
            changed = True
        for key in ("required_slots", "optional_slots"):
            have = {str(item.get("name")) for item in _slot_entries(row.get(key))}
            extra = [item for item in payload[key] if item["name"] not in have]
            if extra:
                row[key] = _slot_entries(row.get(key)) + extra
                changed = True
    if not changed:
        return
    header = (
        "# ژانرهایی که از متن کشف شده‌اند و در کاتالوگ اصلی نبوده‌اند.\n"
        "# با دست حذف نکنید و به قالب‌های discourse.yaml تقلیل ندهید.\n\n"
    )
    dumped = yaml.safe_dump(
        {"discourses": existing},
        allow_unicode=True,
        sort_keys=False,
    )
    target.write_text(header + dumped, encoding="utf-8")


def attach_catalog_discovery(hits: list[DiscourseHit], catalog: list[dict]) -> None:
    """ژانرهایی که قبلاً کشف و وارد کاتالوگ شده‌اند را علامت می‌زند."""
    by_code = {item["code"]: item for item in catalog}
    for hit in hits:
        meta = by_code.get(hit.code)
        if meta is None or not meta.get("discovered"):
            continue
        hit.discovered = True
        if hit.type_schema is None:
            hit.type_schema = schema_from_catalog(meta)


def merge_discourse_hits(
    catalog_hits: list[DiscourseHit],
    novel_hits: list[DiscourseHit],
    catalog: list[dict],
    *,
    max_hits: int,
    do_not_force_fit: bool,
) -> list[DiscourseHit]:
    """نوع نو را کنار کاتالوگ نگه می‌دارد؛ در fallback پیام فرو نمی‌برد."""
    fallback_codes = {item["code"] for item in catalog if item.get("fallback")}
    core = [item for item in catalog_hits if item.code not in fallback_codes]
    fallback = [item for item in catalog_hits if item.code in fallback_codes]
    seen = {item.code for item in core}
    novel = [item for item in novel_hits if item.code not in seen]
    if not do_not_force_fit and core:
        novel = []
    reserved = 1 if novel else 0
    room = max(0, max_hits - reserved)
    hits = core[:room] + novel
    if not hits:
        hits = fallback[:max_hits]
    return hits[:max_hits]
