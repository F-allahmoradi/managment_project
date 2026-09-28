"""اتصال PostgreSQL با سقف زمانی ۱۰ ثانیه برای هر کوئری.

جزئیات پیش‌فرض از config/datasets.yaml می‌آید.
در Production همان فیلدها با POSTGRES_* از محیط جایگزین می‌شوند.
مدت timeout از config/policies.yaml می‌آید.
"""

from pathlib import Path
import os

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


def _overlay_env(source: dict) -> dict:
    """مقادیر اتصال را در صورت وجود متغیر محیط روی YAML می‌گذارد."""
    merged = dict(source)
    host = (os.environ.get("POSTGRES_HOST") or "").strip()
    if host:
        merged["host"] = host
    port = (os.environ.get("POSTGRES_PORT") or "").strip()
    if port:
        merged["port"] = int(port)
    database = (os.environ.get("POSTGRES_DB") or "").strip()
    if database:
        merged["database"] = database
    user = (os.environ.get("POSTGRES_USER") or "").strip()
    if user:
        merged["user"] = user
    if os.environ.get("POSTGRES_PASSWORD") is not None:
        password = os.environ.get("POSTGRES_PASSWORD")
        if str(password).strip() != "":
            merged["password"] = password
    return merged


def load_database_config() -> dict:
    """بلوک اتصال management را از YAML و متغیر محیط برمی‌گرداند."""
    datasets = _read_yaml("config/datasets.yaml")
    source = datasets[_SOURCE_KEY]
    if source.get("type") != "postgresql":
        raise DatabaseError("منبع management باید از نوع postgresql باشد")
    return _overlay_env(source)


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
