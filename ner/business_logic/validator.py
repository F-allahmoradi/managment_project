"""اعتبارسنجی مقدار استخراج‌شده با enum نوع موجودیت.

extractor ذکر خام می‌سازد؛ این ماژول فقط نوعی را نگه می‌دارد که
entity_types واقعاً می‌پذیرد.
"""

from typing import Any

from business_logic.config import load_column_config
from logging_module import logged_step

_SOURCE_KEY = "project_texts"


@logged_step("validate")
def accept_entity_type(value: Any) -> str | None:
    """کد نوع را اگر در entity_types باشد برمی‌گرداند."""
    columns = load_column_config(_SOURCE_KEY)
    allowed = list((columns.get("enums") or {}).get("entity_type") or [])
    if not isinstance(value, str):
        return None
    code = value.strip().upper()
    if code not in allowed:
        return None
    return code


def accept_confidence(value: Any) -> float:
    """اطمینان را به بازه ۰ تا ۱ می‌برد؛ مقدار خراب ۰.۷ می‌شود."""
    try:
        score = float(value) if value is not None else 0.7
    except (TypeError, ValueError):
        score = 0.7
    return min(1.0, max(0.0, score))
