"""اعتبارسنجی ورودی ابزارهای الگوی جلسه."""

from logging_module import logged_step


def validate_create_meeting_schedule(fields: dict) -> dict:
    """ورودی ساخت الگو را با اسکیما بررسی می‌کند."""
    from schemas.meeting.schedule import CreateMeetingScheduleInput

    return CreateMeetingScheduleInput(**fields).model_dump()


def validate_get_meeting_schedule(schedule_id: int) -> int:
    """شناسه خواندن الگو را با اسکیما بررسی می‌کند."""
    from schemas.meeting.schedule import GetMeetingScheduleInput

    return GetMeetingScheduleInput(id=schedule_id).id


def validate_list_meeting_schedules(
    project_id=None,
    is_active=None,
    limit=None,
    offset=None,
) -> dict:
    """صفحه‌بندی و فیلتر فهرست الگو را بررسی می‌کند."""
    from schemas.meeting.schedule import ListMeetingSchedulesInput

    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if is_active is not None:
        payload["is_active"] = is_active
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListMeetingSchedulesInput(**payload).model_dump()


validate_create_meeting_schedule = logged_step("validate")(
    validate_create_meeting_schedule
)
validate_get_meeting_schedule = logged_step("validate")(validate_get_meeting_schedule)
validate_list_meeting_schedules = logged_step("validate")(
    validate_list_meeting_schedules
)
