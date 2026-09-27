"""لودر مشترک کانفیگ ستون‌ها. مسیر YAML این‌جا یک‌بار است."""

from pathlib import Path

import yaml

from errors.crud import InvalidInputError

_ROOT = Path(__file__).resolve().parent.parent


def load_column_config(entity_key: str) -> dict:
    """بلوک یک موجودیت را از columns.yaml برمی‌گرداند."""
    path = _ROOT / "config/columns.yaml"
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    try:
        return payload[entity_key]
    except (TypeError, KeyError) as exc:
        raise InvalidInputError(f"موجودیت {entity_key} در columns.yaml نیست") from exc


def unique_messages_for(entity_key: str) -> dict:
    """پیام‌های قید یکتا را از YAML برمی‌گرداند."""
    return dict(load_column_config(entity_key).get("unique_messages") or {})
