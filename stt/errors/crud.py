"""خطاهای معنایی STT با همان پاکت JSON لایهٔ CRUD.

کلاس‌های مشترک از crud/errors/crud.py بارگذاری می‌شوند.
EMPTY_TRANSCRIPT و خطاهای موتور گفتار مال این سرور است.
"""

import importlib.util
from pathlib import Path

from pydantic import ValidationError

_CRUD_ERRORS_PATH = Path(__file__).resolve().parents[2] / "crud" / "errors" / "crud.py"
_spec = importlib.util.spec_from_file_location(
    "_shared_crud_errors",
    _CRUD_ERRORS_PATH,
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)

CrudError = _mod.CrudError
_base_format_error = _mod.format_error
format_success = _mod.format_success

EMPTY_TRANSCRIPT = "EMPTY_TRANSCRIPT"
CONFIG_ERROR = "CONFIG_ERROR"
STT_TIMEOUT = "STT_TIMEOUT"
STT_UNRECOGNIZED = "STT_UNRECOGNIZED"
STT_PROVIDER_ERROR = "STT_PROVIDER_ERROR"


class EmptyTranscriptError(CrudError):
    """موتور گفتار متن خالی برگرداند."""

    error_code = EMPTY_TRANSCRIPT


class ConfigError(CrudError):
    """ffmpeg یا وابستگی تبدیل صوت پیدا نشد."""

    error_code = CONFIG_ERROR


class SttTimeoutError(CrudError):
    """کاربر در مهلت شروع صحبت نکرد."""

    error_code = STT_TIMEOUT


class SttUnrecognizedError(CrudError):
    """موتور گفتار صدا را تشخیص نداد."""

    error_code = STT_UNRECOGNIZED


class SttProviderError(CrudError):
    """ارتباط با سرویس تبدیل گفتار شکست خورد."""

    error_code = STT_PROVIDER_ERROR


def format_error(exc: BaseException) -> dict:
    """پاکت خطا را می‌سازد؛ متن خام گفتار در پیام نمی‌آید."""
    if isinstance(exc, ValidationError):
        return {
            "status": "error",
            "error_code": INVALID_INPUT,
            "message": "ورودی تبدیل گفتار نامعتبر است",
        }
    if isinstance(exc, ImportError):
        return {
            "status": "error",
            "error_code": CONFIG_ERROR,
            "message": "بارگذاری سرویس محتوا ناموفق بود",
        }
    return _base_format_error(exc)
