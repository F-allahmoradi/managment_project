"""خواندن میزبان و پورت و بازیگر زمین بازی از config/playground.yaml."""

import os
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULTS = {"host": "127.0.0.1", "port": 8777}
_ACTOR_ID_ENV = "MCP_ACTOR_USER_ID"
_ACTOR_USERNAME_ENV = "MCP_ACTOR_USERNAME"


def load_playground_config() -> dict:
    """تنظیم زمین بازی را از YAML می‌خواند."""
    path = _ROOT / "config/playground.yaml"
    settings = dict(_DEFAULTS)
    if not path.exists():
        return settings
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        return settings
    if "host" in raw:
        settings["host"] = str(raw["host"])
    if "port" in raw:
        settings["port"] = int(raw["port"])
    actor_id = raw.get("actor_user_id")
    if actor_id not in (None, ""):
        settings["actor_user_id"] = int(actor_id)
    actor_username = raw.get("actor_username")
    if isinstance(actor_username, str) and actor_username.strip():
        settings["actor_username"] = actor_username.strip()
    return settings


def _discover_actor():
    """اولین کاربر فعال با مجوز ثبت تحلیل را برمی‌گرداند."""
    from repository.connection import open_connection

    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.username
                FROM users u
                JOIN user_roles ur ON ur.user_id = u.id
                JOIN roles r ON r.id = ur.role_id
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE u.is_active
                  AND r.is_active
                  AND p.resource = 'TextAnalysis'
                  AND p.action = 'Create'
                ORDER BY CASE WHEN r.name = 'مدیر کل' THEN 0 ELSE 1 END, u.id
                LIMIT 1
                """
            )
            return cursor.fetchone()
    finally:
        connection.close()


def bind_playground_actor() -> str | None:
    """بازیگر ذخیره را از محیط، YAML، یا اولین مدیر کل می‌گذارد."""
    if (os.environ.get(_ACTOR_ID_ENV) or "").strip():
        return os.environ.get(_ACTOR_ID_ENV)
    if (os.environ.get(_ACTOR_USERNAME_ENV) or "").strip():
        return os.environ.get(_ACTOR_USERNAME_ENV)
    settings = load_playground_config()
    if settings.get("actor_user_id"):
        os.environ[_ACTOR_ID_ENV] = str(settings["actor_user_id"])
        os.environ.pop(_ACTOR_USERNAME_ENV, None)
        return str(settings["actor_user_id"])
    if settings.get("actor_username"):
        os.environ[_ACTOR_USERNAME_ENV] = settings["actor_username"]
        os.environ.pop(_ACTOR_ID_ENV, None)
        return settings["actor_username"]
    try:
        row = _discover_actor()
    except Exception:
        return None
    if row is None:
        return None
    os.environ[_ACTOR_ID_ENV] = str(row[0])
    os.environ.pop(_ACTOR_USERNAME_ENV, None)
    return str(row[1])
