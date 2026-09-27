"""سقف زمانی ۱۰ ثانیه برای کوئری‌های CRUD.

مدت از config/policies.yaml خوانده می‌شود تا در پایتون قفل نشود.
اعمال سقف روی اتصال در services/connection.py است.
"""

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_TIMEOUT_SECONDS = 10


def _read_yaml(relative_path: str) -> dict:
    """یک فایل YAML را از ریشه پروژه می‌خواند.

    ورودی:
        relative_path: مسیر نسبی مثل config/policies.yaml.
    خروجی:
        دیکشنری حاصل از yaml.safe_load.
    فراخوانی‌ها:
        yaml.safe_load.
    علت:
        سقف timeout نباید در چند فایل پایتون تکرار شود.
    """
    path = _ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_policies() -> dict:
    """سیاست timeout و صفحه‌بندی را از policies.yaml برمی‌گرداند.

    ورودی:
        هیچ. مسیر فایل ثابت است.
    خروجی:
        دیکشنری شامل timeout_seconds و pagination.
    فراخوانی‌ها:
        _read_yaml.
    """
    return _read_yaml("config/policies.yaml")


def load_timeout_ms() -> int:
    """سقف اجرای کوئری را به میلی‌ثانیه از policies.yaml برمی‌گرداند.

    ورودی:
        هیچ. کلید timeout_seconds در policies.yaml است.
    خروجی:
        عدد میلی‌ثانیه، مثلاً ۱۰۰۰۰ برای ۱۰ ثانیه.
    فراخوانی‌ها:
        load_policies.
    علت:
        psycopg2 و PostgreSQL statement_timeout را به میلی‌ثانیه می‌گیرند.
    """
    settings = load_policies()
    seconds = settings.get("timeout_seconds", _DEFAULT_TIMEOUT_SECONDS)
    return int(seconds) * 1000
