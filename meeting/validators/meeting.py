"""اعتبارسنجی ورودی ابزارهای نمونهٔ جلسه."""

from logging_module import logged_step


def validate_create_meeting(fields: dict) -> dict:
    """ورودی ساخت جلسه را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import CreateMeetingInput

    return CreateMeetingInput(**fields).model_dump()


def validate_get_meeting(meeting_id: int) -> int:
    """شناسه خواندن جلسه را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import GetMeetingInput

    return GetMeetingInput(id=meeting_id).id


def validate_list_meetings(
    project_id=None,
    status_id=None,
    status=None,
    limit=None,
    offset=None,
) -> dict:
    """صفحه‌بندی و فیلتر فهرست جلسه را بررسی می‌کند."""
    from schemas.meeting.meeting import ListMeetingsInput

    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if status_id is not None:
        payload["status_id"] = status_id
    if status is not None:
        payload["status"] = status
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListMeetingsInput(**payload).model_dump()


def validate_cancel_meeting(meeting_id: int) -> int:
    """شناسه لغو جلسه را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import CancelMeetingInput

    return CancelMeetingInput(id=meeting_id).id


def validate_generate_meetings(fields: dict) -> dict:
    """ورودی تولید نمونه از الگو را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import GenerateMeetingsInput

    return GenerateMeetingsInput(**fields).model_dump()


def validate_record_meeting(fields: dict) -> dict:
    """ورودی ضبط جلسه را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import RecordMeetingInput

    return RecordMeetingInput(**fields).model_dump()


def validate_sync_meeting(fields: dict) -> dict:
    """ورودی همگام‌سازی جلسه را با اسکیما بررسی می‌کند."""
    from schemas.meeting.meeting import SyncMeetingInput

    return SyncMeetingInput(**fields).model_dump()


validate_create_meeting = logged_step("validate")(validate_create_meeting)
validate_get_meeting = logged_step("validate")(validate_get_meeting)
validate_list_meetings = logged_step("validate")(validate_list_meetings)
validate_cancel_meeting = logged_step("validate")(validate_cancel_meeting)
validate_generate_meetings = logged_step("validate")(validate_generate_meetings)
validate_record_meeting = logged_step("validate")(validate_record_meeting)
validate_sync_meeting = logged_step("validate")(validate_sync_meeting)
