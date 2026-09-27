"""خواندن تنظیم لاگ از config/logging.yaml.

مسیر فایل و سطح لاگ در پایتون قفل نمی‌شود تا بدون تغییر کد عوض شود.
"""

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULTS = {
    "level": "INFO",
    "console": True,
    "include_trace_in_response": True,
    "file": {
        "enabled": True,
        "path": "logs/mcp.log",
        "max_bytes": 1_000_000,
        "backup_count": 5,
    },
}


def _merge_defaults(raw) -> dict:
    """مقادیر ناقص YAML را با پیش‌فرض پر می‌کند.

    ورودی:
        raw: خروجی yaml.safe_load؛ ممکن است None باشد.
    خروجی:
        دیکشنری کامل تنظیم لاگ.
    فراخوانی‌ها:
        هیچ.
    علت:
        نبود یک کلید نباید راه‌اندازی سرور را بخواباند.
    """
    settings = dict(_DEFAULTS)
    if not isinstance(raw, dict):
        return settings
    if "level" in raw:
        settings["level"] = raw["level"]
    if "console" in raw:
        settings["console"] = bool(raw["console"])
    if "include_trace_in_response" in raw:
        settings["include_trace_in_response"] = bool(
            raw["include_trace_in_response"]
        )
    file_settings = dict(_DEFAULTS["file"])
    raw_file = raw.get("file")
    if isinstance(raw_file, dict):
        file_settings.update(raw_file)
    settings["file"] = file_settings
    return settings


def load_logging_config() -> dict:
    """تنظیم لاگ را از YAML می‌خواند.

    ورودی:
        هیچ. مسیر فایل ثابت است.
    خروجی:
        دیکشنری شامل level، console، include_trace_in_response و file.
    فراخوانی‌ها:
        yaml.safe_load.
    علت:
        کنسول و فایل هر دو از یک جا روشن و خاموش می‌شوند.
    """
    path = _ROOT / "config/logging.yaml"
    if not path.exists():
        return _merge_defaults(None)
    with path.open(encoding="utf-8") as handle:
        return _merge_defaults(yaml.safe_load(handle))


def resolve_log_path(relative_or_absolute: str) -> Path:
    """مسیر فایل لاگ را نسبت به ریشه پروژه مطلق می‌کند.

    ورودی:
        relative_or_absolute: مقدار path در YAML، مثلاً logs/mcp.log.
    خروجی:
        Path مطلق آمادهٔ ساخت پوشه و باز کردن فایل.
    فراخوانی‌ها:
        Path.resolve.
    علت:
        اجرای سرور از هر cwd باید به همان فایل برسد.
    """
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    return (_ROOT / path).resolve()
