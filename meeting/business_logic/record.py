"""وصل کردن محتوای ضبط به جلسه.

contents در crud ساخته می‌شود؛ اینجا فقط content_id روی meetings
می‌نشیند و وضعیت به ضبط شده می‌رود.
"""

from datetime import datetime

from errors.crud import InvalidInputError, MeetingNotFoundError
from logging_module import logged_step
from repository.db import run_query
from services.audit_log import ACTION_UPDATE, record_audit_on
from services.content import fetch_content

from business_logic.meetings import require_meeting_access, require_meeting_manager
from business_logic.repository import attach_recording_on, fetch_recorded_status_id

_RECORDABLE = frozenset({"برنامه‌ریزی شده", "برگزار شده", "ضبط شده"})
_ALLOWED_KINDS = frozenset({"TEXT", "VOICE"})


def record_meeting(meeting_id: int, content_id: int, actor_id: int) -> int:
    """محتوای موجود را به جلسه وصل می‌کند؛ وضعیت → ضبط شده."""
    meeting = require_meeting_access(actor_id, meeting_id)
    require_meeting_manager(actor_id, meeting)
    if meeting["status_name"] == "لغو شده":
        raise InvalidInputError("جلسهٔ لغو شده ضبط نمی‌شود")
    if meeting["status_name"] not in _RECORDABLE:
        raise InvalidInputError("فقط جلسهٔ برنامه‌ریزی‌شده یا برگزارشده ضبط می‌شود")
    if meeting["sync_status"] == "SYNCED":
        raise InvalidInputError("جلسهٔ همگام‌شده را نمی‌توان دوباره ضبط کرد")
    content = fetch_content(content_id)
    if content["content_kind_code"] not in _ALLOWED_KINDS:
        raise InvalidInputError("ضبط جلسه فقط TEXT یا VOICE می‌پذیرد")
    status_id = fetch_recorded_status_id()
    held_at = meeting.get("held_at") or datetime.now()

    def work(connection):
        updated = attach_recording_on(
            connection,
            meeting_id,
            content_id,
            status_id,
            held_at,
        )
        if updated is None:
            raise MeetingNotFoundError(f"جلسه با شناسه {meeting_id} پیدا نشد")
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "Meeting",
            meeting_id,
            {
                "content_id": meeting.get("content_id"),
                "status_name": meeting["status_name"],
            },
            {"content_id": content_id, "status_name": "ضبط شده"},
        )
        return updated

    return run_query(work)


record_meeting = logged_step("update")(record_meeting)
