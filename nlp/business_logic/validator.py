"""اعتبارسنجی کد کاتالوگ و اطمینان استخراج."""

from typing import Any

from business_logic.config import (
    load_column_config,
    load_facts_catalog,
    load_frames_catalog,
    load_quotes_catalog,
)

_SOURCE_KEY = "project_texts"


def accept_confidence(value: Any) -> float:
    """اطمینان را به بازه ۰ تا ۱ می‌برد؛ مقدار خراب ۰.۷ می‌شود."""
    try:
        score = float(value) if value is not None else 0.7
    except (TypeError, ValueError):
        score = 0.7
    return min(1.0, max(0.0, score))


def _lookup(catalog: list[dict], value: Any) -> dict | None:
    """کد یا نام یا alias را به ردیف کاتالوگ می‌برد."""
    if not isinstance(value, str):
        return None
    key = value.strip()
    if not key:
        return None
    lowered = key.lower()
    for item in catalog:
        code = str(item["code"])
        if key == code or lowered == code.lower():
            return item
        if key == item.get("name"):
            return item
        for alias in item.get("aliases") or []:
            if key == alias or lowered == str(alias).lower():
                return item
    return None


def accept_kind(value: Any) -> dict | None:
    """نوع فکت مجاز را برمی‌گرداند."""
    columns = load_column_config(_SOURCE_KEY)
    allowed = set((columns.get("enums") or {}).get("fact_kind") or [])
    found = _lookup(load_facts_catalog()["kinds"], value)
    if found is None or found["code"] not in allowed:
        return None
    return found


def accept_unit(value: Any) -> dict | None:
    """واحد مقدار را اگر در کاتالوگ باشد برمی‌گرداند."""
    if value in (None, ""):
        return None
    return _lookup(load_facts_catalog()["units"], value)


def accept_grounding(value: Any) -> dict | None:
    """صراحت فکت را برمی‌گرداند."""
    return _lookup(load_facts_catalog()["groundings"], value)


def accept_role(value: Any) -> dict:
    """نقش مقدار را برمی‌گرداند؛ پیش‌فرض none."""
    found = _lookup(load_facts_catalog()["quantity_roles"], value)
    if found is not None:
        return found
    return next(
        item
        for item in load_facts_catalog()["quantity_roles"]
        if item.get("fallback") or item["code"] == "none"
    )


def accept_derivation(value: Any) -> dict | None:
    """عمل استنتاج عددی را برمی‌گرداند."""
    if value in (None, ""):
        return None
    return _lookup(load_facts_catalog()["derivations"], value)


def accept_quote_mode(value: Any) -> dict | None:
    """شیوه نقل را برمی‌گرداند."""
    return _lookup(load_quotes_catalog()["modes"], value)


def accept_scope(value: Any) -> dict | None:
    """محدوده را برمی‌گرداند."""
    return _lookup(load_frames_catalog()["scopes"], value)


def accept_process(value: Any) -> dict | None:
    """فرآیند را برمی‌گرداند."""
    return _lookup(load_frames_catalog()["processes"], value)
