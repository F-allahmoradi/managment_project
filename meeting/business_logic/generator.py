"""تولید نمونهٔ جلسه از روی الگو.

اگر ساعت همان هفته پر باشد جلسه ساخته نمی‌شود و هفتهٔ بعد پیشنهاد می‌شود.
"""

from datetime import date, datetime

from errors.crud import InvalidInputError
from logging_module import logged_step
from repository.db import json_safe, run_query
from services.audit_log import ACTION_CREATE, record_audit_on

from business_logic.calendar import (
    DAY_NAMES,
    isoformat_naive,
    occurrence_in_week,
)
from business_logic.meetings import (
    find_slot_conflict,
    resolve_visibility,
    scheduled_end,
    suggest_after_conflict,
)
from business_logic.repository import (
    fetch_planned_status_id,
    insert_meeting_on,
)
from business_logic.schedules import fetch_schedule, require_schedule_owner


def _date_of(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _schedule_covers(schedule: dict, target: date) -> bool:
    """تاریخ را با بازهٔ اعتبار الگو می‌سنجد."""
    start = _date_of(schedule["effective_from"])
    if target < start:
        return False
    until = schedule.get("effective_until")
    if until is None:
        return True
    return target <= _date_of(until)


def default_meeting_title(schedule: dict, scheduled_at: datetime) -> str:
    """عنوان پیش‌فرض نمونه از نوع و روز الگو."""
    type_name = schedule.get("meeting_type_name") or "جلسه"
    day_name = DAY_NAMES.get(int(schedule["day_of_week"]), "")
    stamp = scheduled_at.strftime("%Y-%m-%d %H:%M")
    if day_name:
        return f"{type_name} {day_name} {stamp}"
    return f"{type_name} {stamp}"


def generate_meetings(
    schedule_id: int,
    actor_id: int,
    weeks_ahead: int = 1,
    title=None,
    visibility=None,
    now=None,
) -> dict:
    """از الگو یک نمونه برای هفتهٔ هدف می‌سازد یا تداخل را برمی‌گرداند.

    خروجی در صورت ساخت: created=True و id.
    در صورت پر بودن ساعت: created=False و suggested_at هفتهٔ بعد.
    """
    schedule = fetch_schedule(schedule_id)
    require_schedule_owner(actor_id, schedule)
    if not schedule.get("is_active", True):
        raise InvalidInputError("این الگو غیرفعال است")
    clock = now or datetime.now()
    if getattr(clock, "tzinfo", None) is not None:
        clock = clock.replace(tzinfo=None)
    duration = int(schedule["duration_minutes"])
    start, end = occurrence_in_week(
        int(schedule["day_of_week"]),
        schedule["start_time"],
        duration,
        weeks_ahead,
        clock,
    )
    if not _schedule_covers(schedule, start.date()):
        raise InvalidInputError("این تاریخ بیرون از بازهٔ اعتبار الگو است")
    suggestion = suggest_after_conflict(start, duration)
    conflict = find_slot_conflict(actor_id, start, end)
    if conflict is not None:
        return {
            "created": False,
            "conflict": True,
            "requested_at": suggestion["requested_at"],
            "suggested_at": suggestion["suggested_at"],
            "suggested_end_at": suggestion["suggested_end_at"],
            "conflicting_meeting_id": conflict["id"],
        }
    project_id = schedule.get("project_id")
    vis_fields = {"visibility": visibility} if visibility else {}
    resolved_visibility = resolve_visibility(vis_fields, project_id)
    status_id = fetch_planned_status_id()
    meeting_title = title or default_meeting_title(schedule, start)
    payload = {
        "project_id": project_id,
        "manager_user_id": actor_id,
        "schedule_id": schedule_id,
        "meeting_type_id": schedule["meeting_type_id"],
        "status_id": status_id,
        "visibility": resolved_visibility,
        "title": meeting_title,
        "scheduled_at": start,
        "scheduled_end_at": end,
        "duration_minutes": duration,
        "location": None,
    }

    def work(connection):
        new_id = insert_meeting_on(connection, payload)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "Meeting",
            new_id,
            None,
            {
                "schedule_id": schedule_id,
                "scheduled_at": json_safe(start),
                "generated": True,
            },
        )
        return new_id

    new_id = run_query(work)
    return {
        "created": True,
        "conflict": False,
        "id": new_id,
        "scheduled_at": isoformat_naive(start),
        "scheduled_end_at": isoformat_naive(end),
        "title": meeting_title,
    }


generate_meetings = logged_step("insert")(generate_meetings)
