"""تنظیم سرور HTTP از متغیر محیط.

پیش‌فرض میزبان 0.0.0.0 است تا گوشی در شبکه محلی به API برسد.
وب Vite همچنان از پروکسی localhost استفاده می‌کند.
"""

import os

DEFAULT_DOMAINS = (
    "crud",
    "meeting",
    "finance",
    "reminder",
    "stats",
    "stt",
    "ner",
    "nlp",
    "embedding",
)
OPTIONAL_DOMAINS = ()
ALL_DOMAINS = DEFAULT_DOMAINS + OPTIONAL_DOMAINS


def load_settings() -> dict:
    """میزبان، درگاه، CORS، مدت نشست و دامنه‌های فعال را می‌خواند."""
    origins = _split_csv(os.environ.get("API_CORS_ORIGINS") or "*")
    domains = _domains(os.environ.get("API_DOMAINS") or "")
    return {
        "host": (os.environ.get("API_HOST") or "0.0.0.0").strip(),
        "port": _positive_int(os.environ.get("API_PORT"), 8080),
        "cors_origins": origins or ["*"],
        "session_ttl_hours": _positive_int(os.environ.get("API_SESSION_TTL_HOURS"), 336),
        "tool_timeout_seconds": _positive_int(os.environ.get("API_TOOL_TIMEOUT_SECONDS"), 300),
        "max_body_bytes": _positive_int(os.environ.get("API_MAX_BODY_BYTES"), 8 * 1024 * 1024),
        "domains": domains,
    }


def _domains(raw: str) -> tuple:
    text = raw.strip().lower()
    if not text:
        return DEFAULT_DOMAINS
    if text == "all":
        return ALL_DOMAINS
    chosen = []
    for name in _split_csv(text):
        if name not in ALL_DOMAINS:
            raise ValueError(f"دامنه API ناشناخته است: {name}")
        if name not in chosen:
            chosen.append(name)
    if not chosen:
        return DEFAULT_DOMAINS
    return tuple(chosen)


def _split_csv(raw: str) -> list:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _positive_int(raw, default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    value = int(str(raw).strip())
    if value < 1:
        raise ValueError("تنظیم عددی API باید بزرگ‌تر از صفر باشد")
    return value
