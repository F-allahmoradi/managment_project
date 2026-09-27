"""اتصال PostgreSQL با سقف زمانی ۱۰ ثانیه برای هر کوئری.

جزئیات host و رمز از config/datasets.yaml خوانده می‌شود.
مدت timeout از config/policies.yaml می‌آید.
"""

from pathlib import Path

import psycopg2
import yaml

from errors.crud import DatabaseError
from middleware.query_timeout import load_timeout_ms

_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_KEY = "management"


def _read_yaml(relative_path: str) -> dict:
    """یک فایل YAML را از ریشهٔ crud می‌خواند."""
    path = _ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_database_config() -> dict:
    """بلوک اتصال management را از datasets.yaml برمی‌گرداند."""
    datasets = _read_yaml("config/datasets.yaml")
    source = datasets[_SOURCE_KEY]
    if source.get("type") != "postgresql":
        raise DatabaseError("منبع management باید از نوع postgresql باشد")
    return source


def open_connection():
    """اتصال کوتاه‌عمر با statement_timeout باز می‌کند."""
    source = load_database_config()
    timeout_ms = load_timeout_ms()
    try:
        return psycopg2.connect(
            host=source["host"],
            port=source["port"],
            dbname=source["database"],
            user=source["user"],
            password=source["password"],
            options=f"-c statement_timeout={timeout_ms}",
        )
    except psycopg2.Error as exc:
        raise DatabaseError(f"اتصال به PostgreSQL ناموفق بود: {exc}") from exc
