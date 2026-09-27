"""خطاهای معنایی جلسات با همان پاکت JSON لایهٔ CRUD.

کلاس‌های مشترک از crud/errors/crud.py بارگذاری می‌شوند تا
auth و سرویس‌های کراد همان error_code را ببینند.
"""

import importlib.util
from pathlib import Path

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
MEETING_SCHEDULE_NOT_FOUND = "MEETING_SCHEDULE_NOT_FOUND"
MEETING_PARTICIPANT_NOT_FOUND = "MEETING_PARTICIPANT_NOT_FOUND"
MEETING_SLOT_CONFLICT = "MEETING_SLOT_CONFLICT"


class MeetingNotFoundError(CrudError):
    """جلسه با شناسه داده‌شده در meetings نیست."""

    error_code = MEETING_NOT_FOUND


class MeetingScheduleNotFoundError(CrudError):
    """الگوی جلسه با شناسه داده‌شده در meeting_schedules نیست."""

    error_code = MEETING_SCHEDULE_NOT_FOUND


class MeetingParticipantNotFoundError(CrudError):
    """شرکت‌کننده با شناسه داده‌شده در meeting_participants نیست."""

    error_code = MEETING_PARTICIPANT_NOT_FOUND


class MeetingSlotConflictError(CrudError):
    """ساعت درخواستی با جلسهٔ دیگری از همان مدیر تداخل دارد."""

    error_code = MEETING_SLOT_CONFLICT

    def __init__(self, message: str, requested_at=None, suggested_at=None) -> None:
        super().__init__(message)
        self.requested_at = requested_at
        self.suggested_at = suggested_at


def format_error(exc: BaseException) -> dict:
    """پاکت خطا را می‌سازد و برای تداخل ساعت، پیشنهاد هفتهٔ بعد را هم می‌گذارد."""
    payload = _base_format_error(exc)
    if isinstance(exc, MeetingSlotConflictError):
        if exc.requested_at is not None:
            payload["requested_at"] = exc.requested_at
        if exc.suggested_at is not None:
            payload["suggested_at"] = exc.suggested_at
    return payload
