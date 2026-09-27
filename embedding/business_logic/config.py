"""خواندن YAML امبدینگ: مدل برداری و کلید API.

جزئیات host و رمز در پایتون قفل نمی‌شود. کلید API در لاگ نمی‌آید.
"""

from pathlib import Path
import json
import os

import yaml

from errors.crud import ConfigError

_ROOT = Path(__file__).resolve().parent.parent
_CURSOR_SERVER = "management-embedding"
EMBEDDING_DIMENSIONS = 1536


def _read_yaml(relative_path: str) -> dict:
    """یک فایل YAML را از ریشه سرور می‌خواند."""
    path = _ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ConfigError(f"فایل {relative_path} باید یک شیء YAML باشد")
    return loaded


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
    merged: dict[str, str] = {}
    for name in (_CURSOR_SERVER, "management-nlp"):
        block = servers.get(name)
        if not isinstance(block, dict):
            continue
        env = block.get("env")
        if not isinstance(env, dict):
            continue
        for key, value in env.items():
            if value is None:
                continue
            text = str(value).strip()
            if text and str(key) not in merged:
                merged[str(key)] = text
    return merged


def load_llm_config() -> dict:
    """تنظیم مدل امبدینگ را از llm.yaml و متغیر محیطی کلید می‌خواند."""
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
    env_name = str(raw.get("api_key_env") or "EMBEDDING_API_KEY")
    api_key = (
        os.environ.get(env_name)
        or os.environ.get("NLP_LLM_API_KEY")
        or os.environ.get("AVALAI_API_KEY")
        or cursor_env.get(env_name)
        or cursor_env.get("NLP_LLM_API_KEY")
        or cursor_env.get("AVALAI_API_KEY")
        or ""
    )
    allow_missing = bool(raw.get("allow_missing_api_key", False))
    if not api_key and not allow_missing:
        raise ConfigError(f"کلید مدل امبدینگ در متغیر {env_name} نیست")
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
        "embedding_model": str(
            os.environ.get("EMBEDDING_MODEL")
            or cursor_env.get("EMBEDDING_MODEL")
            or raw.get("embedding_model")
            or "text-embedding-3-small"
        ).strip(),
        "embedding_timeout_seconds": int(
            raw.get("embedding_timeout_seconds")
            if raw.get("embedding_timeout_seconds") is not None
            else (timeout if timeout is not None else 60)
        ),
    }


def load_llm_public() -> dict:
    """نام مدل امبدینگ و آدرس سرویس را بدون کلید API برمی‌گرداند."""
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
        "embedding_model": str(
            os.environ.get("EMBEDDING_MODEL")
            or cursor_env.get("EMBEDDING_MODEL")
            or raw.get("embedding_model")
            or ""
        ),
    }
