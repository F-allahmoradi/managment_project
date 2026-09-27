"""خطاهای معنایی امبدینگ با همان پاکت JSON لایهٔ CRUD.

کلاس‌های مشترک از crud/errors/crud.py بارگذاری می‌شوند.
LLM_ERROR و EMPTY_TRANSCRIPT مال این سرور است؛ INSERT تحلیل اینجا نیست.
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

MEETING_NOT_FOUND = "MEETING_NOT_FOUND"
LLM_ERROR = "LLM_ERROR"
EMPTY_TRANSCRIPT = "EMPTY_TRANSCRIPT"
CONFIG_ERROR = "CONFIG_ERROR"


class MeetingNotFoundError(CrudError):
    """جلسه با شناسه داده‌شده در meetings نیست."""

    error_code = MEETING_NOT_FOUND


class LlmError(CrudError):
    """فراخوانی مدل زبانی شکست خورد. پیام بدون کلید و بدون متن جلسه است."""

    error_code = LLM_ERROR


class EmptyTranscriptError(CrudError):
    """ضبط جلسه text_body ندارد؛ رونویسی صوت در این گام نیست."""

    error_code = EMPTY_TRANSCRIPT


class ConfigError(CrudError):
    """YAML ناقص است یا کلید مدل تنظیم نشده."""

    error_code = CONFIG_ERROR


def format_error(exc: BaseException) -> dict:
    """پاکت خطا را می‌سازد؛ متن خام جلسه و رمز در پیام نمی‌آید."""
    if isinstance(exc, ValidationError):
        return {
            "status": "error",
            "error_code": INVALID_INPUT,
            "message": "ورودی امبدینگ نامعتبر است",
        }
    return _base_format_error(exc)
