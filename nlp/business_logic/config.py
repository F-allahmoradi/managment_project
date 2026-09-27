"""خواندن YAML پردازش زبانی: ستون‌ها، مدل، کاتالوگ.

جزئیات host و رمز در پایتون قفل نمی‌شود. کلید API در لاگ نمی‌آید.
"""

from pathlib import Path
import json
import os

import yaml

from errors.crud import ConfigError

_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_KEY = "project_texts"
_CURSOR_SERVER = "management-nlp"


def _read_yaml(relative_path: str) -> dict:
    """یک فایل YAML را از ریشه سرور می‌خواند."""
    path = _ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ConfigError(f"فایل {relative_path} باید یک شیء YAML باشد")
    return loaded


def load_column_config(source_key: str = _SOURCE_KEY) -> dict:
    """بلوک منبع را از columns.yaml برمی‌گرداند."""
    columns = _read_yaml("config/columns.yaml")
    block = columns.get(source_key)
    if not isinstance(block, dict):
        raise ConfigError(f"کلید {source_key} در columns.yaml نیست")
    extractable = block.get("extractable") or []
    if not extractable:
        raise ConfigError(f"لیست فیلدهای قابل‌استخراج برای {source_key} خالی است")
    return block


def _cursor_llm_env() -> dict[str, str]:
    """env سرور را از mcp.json لوکال Cursor می‌خواند؛ خود کلید لاگ نمی‌شود."""
    path = Path.home() / ".cursor" / "mcp.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    servers = loaded.get("mcpServers") if isinstance(loaded, dict) else None
    if not isinstance(servers, dict):
        return {}
    block = servers.get(_CURSOR_SERVER)
    if not isinstance(block, dict):
        return {}
    env = block.get("env")
    if not isinstance(env, dict):
        return {}
    filled: dict[str, str] = {}
    for key, value in env.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            filled[str(key)] = text
    return filled


def load_llm_config() -> dict:
    """تنظیم مدل را از llm.yaml و متغیر محیطی کلید می‌خواند."""
    raw = _read_yaml("config/llm.yaml")
    cursor_env = _cursor_llm_env()
    base_url = str(
        os.environ.get("AVALAI_BASE_URL")
        or cursor_env.get("AVALAI_BASE_URL")
        or raw.get("base_url")
        or ""
    ).rstrip("/")
    model = str(
        os.environ.get("AI_MODEL")
        or cursor_env.get("AI_MODEL")
        or raw.get("model")
        or ""
    ).strip()
    if not base_url:
        raise ConfigError("base_url در llm.yaml یا AVALAI_BASE_URL خالی است")
    if not model:
        raise ConfigError("model در llm.yaml یا AI_MODEL خالی است")
    env_name = str(raw.get("api_key_env") or "NLP_LLM_API_KEY")
    api_key = (
        os.environ.get(env_name)
        or os.environ.get("AVALAI_API_KEY")
        or cursor_env.get(env_name)
        or cursor_env.get("AVALAI_API_KEY")
        or ""
    )
    allow_missing = bool(raw.get("allow_missing_api_key", False))
    if not api_key and not allow_missing:
        raise ConfigError(f"کلید مدل زبانی در متغیر {env_name} نیست")
    timeout = raw.get("timeout_seconds")
    temperature = raw.get("temperature")
    return {
        "base_url": base_url,
        "model": model,
        "timeout_seconds": int(timeout) if timeout is not None else 45,
        "temperature": float(temperature) if temperature is not None else 0,
        "api_key": api_key,
        "api_key_env": env_name,
        "json_response_format": bool(raw.get("json_response_format", True)),
    }


def load_llm_public() -> dict:
    """نام مدل و آدرس سرویس را بدون کلید API برمی‌گرداند."""
    raw = _read_yaml("config/llm.yaml")
    cursor_env = _cursor_llm_env()
    return {
        "model": str(
            os.environ.get("AI_MODEL")
            or cursor_env.get("AI_MODEL")
            or raw.get("model")
            or ""
        ),
        "base_url": str(
            os.environ.get("AVALAI_BASE_URL")
            or cursor_env.get("AVALAI_BASE_URL")
            or raw.get("base_url")
            or ""
        ).rstrip("/"),
    }


def _named_codes(raw: dict, key: str) -> list[dict]:
    """لیست lookup کد/نام را از YAML می‌خواند."""
    items = raw.get(key)
    if not isinstance(items, list) or not items:
        raise ConfigError(f"لیست {key} خالی است")
    catalog: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        if not code or not name:
            continue
        aliases = []
        for alias in item.get("aliases") or []:
            text = str(alias or "").strip()
            if text:
                aliases.append(text)
        catalog.append(
            {
                "code": code,
                "name": name,
                "definition": str(item.get("definition") or "").strip(),
                "fallback": bool(item.get("fallback")),
                "aliases": aliases,
            }
        )
    if not catalog:
        raise ConfigError(f"هیچ مقدار معتبری برای {key} نیست")
    return catalog


def load_facts_catalog() -> dict:
    """نوع فکت، واحد، صراحت و نقش مقدار را می‌خواند."""
    raw = _read_yaml("config/facts.yaml")
    return {
        "kinds": _named_codes(raw, "kinds"),
        "units": _named_codes(raw, "units"),
        "groundings": _named_codes(raw, "groundings"),
        "quantity_roles": _named_codes(raw, "quantity_roles"),
        "derivations": _named_codes(raw, "derivations"),
        "rules": [
            str(item).strip()
            for item in (raw.get("rules") or [])
            if str(item).strip()
        ],
    }


def load_quotes_catalog() -> dict:
    """شیوه نقل‌قول را می‌خواند."""
    raw = _read_yaml("config/quotes.yaml")
    return {
        "modes": _named_codes(raw, "modes"),
        "rules": [
            str(item).strip()
            for item in (raw.get("rules") or [])
            if str(item).strip()
        ],
    }


def load_frames_catalog() -> dict:
    """محدوده و فرآیند را می‌خواند."""
    raw = _read_yaml("config/frames.yaml")
    return {
        "scopes": _named_codes(raw, "scopes"),
        "processes": _named_codes(raw, "processes"),
        "rules": [
            str(item).strip()
            for item in (raw.get("rules") or [])
            if str(item).strip()
        ],
    }


def load_layer_config() -> dict:
    """وضعیت روشن/خاموش لایه‌ها را از layers.yaml می‌خواند."""
    raw = _read_yaml("config/layers.yaml")
    if not raw:
        raise ConfigError("layers.yaml خالی است")
    return raw


def load_source() -> dict:
    """بلوک کاتالوگ project_texts را بدون رمز برمی‌گرداند."""
    datasets = _read_yaml("config/datasets.yaml")
    source = datasets.get(_SOURCE_KEY)
    if not isinstance(source, dict):
        raise ConfigError("کلید project_texts در datasets.yaml نیست")
    return source
