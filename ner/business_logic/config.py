"""خواندن YAML استخراج جلسه: ستون‌ها، مدل زبانی، کاتالوگ.

جزئیات host و رمز در پایتون قفل نمی‌شود. کلید API در لاگ نمی‌آید.
"""

from pathlib import Path
from typing import Any
import json
import os

import yaml

from errors.crud import ConfigError

_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_KEY = "project_texts"
_CURSOR_SERVER = "management-ner"


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
    extractable = block.get("extractable") or block.get("analyzable") or []
    if not extractable:
        raise ConfigError(f"لیست فیلدهای قابل‌استخراج برای {source_key} خالی است")
    return block


def load_entity_config() -> dict:
    """هم‌معنی enum را از entities.yaml می‌خواند؛ راهنمای مدل است نه regex."""
    return _read_yaml("config/entities.yaml")


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
    env_name = str(raw.get("api_key_env") or "NER_LLM_API_KEY")
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


def _parse_topic_items(items: list) -> list[dict]:
    """ردیف‌های YAML موضوع را یکدست می‌کند."""
    catalog: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        definition = str(item.get("definition") or "").strip()
        description = str(item.get("description") or "").strip()
        if not code or not name or not definition:
            continue
        parts = code.split(".")
        parent_code = ".".join(parts[:-1]) if len(parts) > 1 else None
        aliases = []
        for alias in item.get("aliases") or []:
            text = str(alias or "").strip()
            if text:
                aliases.append(text)
        cues = []
        for cue in item.get("cues") or []:
            text = str(cue or "").strip()
            if text:
                cues.append(text)
        catalog.append(
            {
                "code": code,
                "name": name,
                "level": int(item.get("level") or 1),
                "parent_code": parent_code,
                "aliases": aliases,
                "cues": cues,
                "fallback": bool(item.get("fallback")),
                "discovered": bool(item.get("discovered")),
                "definition": definition,
                "description": description,
                "contrast": _slot_list(item.get("contrast")),
                "accept_example": str(item.get("accept_example") or "").strip(),
                "reject_example": str(item.get("reject_example") or "").strip(),
            }
        )
    return catalog


def load_topic_discovery() -> dict:
    """سیاست کشف موضوع نو را از topics.yaml می‌خواند."""
    raw = _read_yaml("config/topics.yaml")
    block = raw.get("discovery")
    if not isinstance(block, dict):
        block = {}
    catalog_file = str(block.get("catalog_file") or "discovered_topics.yaml").strip()
    if not catalog_file or "/" in catalog_file or "\\" in catalog_file:
        catalog_file = "discovered_topics.yaml"
    rules = []
    for item in block.get("rules") or []:
        text = str(item or "").strip()
        if text:
            rules.append(text)
    return {
        "enabled": bool(block.get("enabled", True)),
        "persist": bool(block.get("persist", True)),
        "do_not_force_fit": bool(block.get("do_not_force_fit", True)),
        "catalog_file": catalog_file,
        "rules": rules,
    }


def discovered_topic_path() -> Path:
    """مسیر فایل موضوع‌های کشف‌شده کنار کاتالوگ اصلی."""
    name = load_topic_discovery()["catalog_file"]
    return _ROOT / "config" / name


def load_topic_catalog() -> list[dict]:
    """فهرست حوزه را از topics.yaml به‌علاوه موضوع‌های کشف‌شده می‌خواند."""
    raw = _read_yaml("config/topics.yaml")
    items = raw.get("topics")
    if not isinstance(items, list) or not items:
        raise ConfigError("لیست topics در topics.yaml خالی است")
    catalog = _parse_topic_items(items)
    if not catalog:
        raise ConfigError("هیچ موضوع معتبری در topics.yaml نیست")
    seen = {item["code"] for item in catalog}
    extra_path = discovered_topic_path()
    if extra_path.is_file():
        loaded = _read_yaml("config/" + str(load_topic_discovery()["catalog_file"]))
        extra_items = loaded.get("topics") if isinstance(loaded, dict) else None
        for item in _parse_topic_items(extra_items or []):
            if item["code"] in seen:
                continue
            item["discovered"] = True
            catalog.append(item)
            seen.add(item["code"])
    return catalog


def _named_codes(raw: dict, key: str, *, with_level: bool = False) -> list[dict]:
    """لیست lookup کد/نام را از YAML می‌خواند."""
    items = raw.get(key)
    if not isinstance(items, list) or not items:
        raise ConfigError(f"لیست {key} در stance.yaml خالی است")
    catalog: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        if not code or not name:
            continue
        row = {"code": code, "name": name}
        if with_level:
            row["level"] = int(item.get("level") or 1)
        catalog.append(row)
    if not catalog:
        raise ConfigError(f"هیچ مقدار معتبری برای {key} در stance.yaml نیست")
    return catalog


def load_stance_catalog() -> dict:
    """قطبیت، شدت و هیجان را از stance.yaml می‌خواند؛ همان کدهای seed."""
    raw = _read_yaml("config/stance.yaml")
    return {
        "polarities": _named_codes(raw, "polarities"),
        "intensity_levels": _named_codes(raw, "intensity_levels", with_level=True),
        "emotions": _named_codes(raw, "emotions"),
    }


def _slot_list(raw: Any) -> list[str]:
    """لیست رشته را از YAML می‌خواند."""
    if not isinstance(raw, list):
        return []
    slots: list[str] = []
    for item in raw:
        text = str(item or "").strip()
        if text:
            slots.append(text)
    return slots


def _slot_entries(raw: Any) -> list[dict]:
    """نقش‌ها را با توضیح اختیاری می‌خواند."""
    if not isinstance(raw, list):
        return []
    entries: list[dict] = []
    for item in raw:
        if isinstance(item, str):
            name = item.strip()
            if name:
                entries.append({"name": name, "description": ""})
            continue
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        entries.append(
            {
                "name": name,
                "description": str(item.get("description") or "").strip(),
            }
        )
    return entries


def _speech_catalog(relative_path: str, key: str) -> list[dict]:
    """کاتالوگ ژانر یا نیت را با نقش و اولویت می‌خواند."""
    raw = _read_yaml(relative_path)
    items = raw.get(key)
    if not isinstance(items, list) or not items:
        raise ConfigError(f"لیست {key} در {relative_path} خالی است")
    catalog: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        definition = str(item.get("definition") or "").strip()
        description = str(item.get("description") or "").strip()
        if not code or not name or not definition or code in seen:
            continue
        aliases = _slot_list(item.get("aliases"))
        if name not in aliases:
            aliases.insert(0, name)
        catalog.append(
            {
                "code": code,
                "name": name,
                "priority": int(item.get("priority") or 0),
                "fallback": bool(item.get("fallback")),
                "discovered": bool(item.get("discovered")),
                "definition": definition,
                "description": description,
                "required_slots": _slot_entries(item.get("required_slots")),
                "optional_slots": _slot_entries(item.get("optional_slots")),
                "contrast": _slot_list(item.get("contrast")),
                "aliases": aliases,
                "accept_example": str(item.get("accept_example") or "").strip(),
                "reject_example": str(item.get("reject_example") or "").strip(),
            }
        )
        seen.add(code)
    if not catalog:
        raise ConfigError(f"هیچ مقدار معتبری برای {key} در {relative_path} نیست")
    catalog.sort(key=lambda row: -int(row["priority"]))
    return catalog


def load_discourse_discovery() -> dict:
    """سیاست کشف ژانر نو را از discourse.yaml می‌خواند."""
    raw = _read_yaml("config/discourse.yaml")
    block = raw.get("discovery")
    if not isinstance(block, dict):
        block = {}
    catalog_file = str(block.get("catalog_file") or "discovered_discourses.yaml").strip()
    if not catalog_file or "/" in catalog_file or "\\" in catalog_file:
        catalog_file = "discovered_discourses.yaml"
    rules = []
    for item in block.get("rules") or []:
        text = str(item or "").strip()
        if text:
            rules.append(text)
    min_slots = block.get("min_required_slots")
    min_confidence = block.get("min_confidence")
    return {
        "enabled": bool(block.get("enabled", True)),
        "persist": bool(block.get("persist", True)),
        "do_not_force_fit": bool(block.get("do_not_force_fit", True)),
        "require_in_text": bool(block.get("require_in_text", True)),
        "min_required_slots": int(min_slots) if min_slots is not None else 2,
        "min_confidence": float(min_confidence) if min_confidence is not None else 0.7,
        "catalog_file": catalog_file,
        "rules": rules,
    }


def discovered_discourse_path() -> Path:
    """مسیر فایل ژانرهای کشف‌شده کنار کاتالوگ اصلی."""
    name = load_discourse_discovery()["catalog_file"]
    return _ROOT / "config" / name


def _optional_speech_catalog(relative_path: str, key: str) -> list[dict]:
    """کاتالوگ اختیاری را می‌خواند؛ نبود فایل یعنی هنوز نوعی کشف نشده."""
    path = _ROOT / relative_path
    if not path.is_file():
        return []
    try:
        return _speech_catalog(relative_path, key)
    except ConfigError:
        return []


def load_discourse_catalog() -> list[dict]:
    """ژانر متن را از discourse.yaml به‌علاوه نوع‌های کشف‌شده می‌خواند."""
    catalog = _speech_catalog("config/discourse.yaml", "discourses")
    seen = {item["code"] for item in catalog}
    extra_path = "config/" + str(load_discourse_discovery()["catalog_file"])
    for item in _optional_speech_catalog(extra_path, "discourses"):
        if item["code"] in seen:
            continue
        item["discovered"] = True
        catalog.append(item)
        seen.add(item["code"])
    catalog.sort(key=lambda row: -int(row["priority"]))
    return catalog


def load_intent_catalog() -> list[dict]:
    """نیت گوینده را از intents.yaml می‌خواند؛ همان کدهای فعال seed."""
    return _speech_catalog("config/intents.yaml", "intents")


def load_rhetoric_catalog() -> list[dict]:
    """صنعت بیان را از rhetoric.yaml می‌خواند؛ همان کدهای فعال seed."""
    return _speech_catalog("config/rhetoric.yaml", "rhetorics")


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
