"""دامنهٔ الگوی تکرار جلسه.

روز و ساعت عادت مدیر است؛ نمونهٔ جلسه از generate_meetings می‌آید.
"""

from datetime import date

from errors.crud import (
    InvalidInputError,
    MeetingScheduleNotFoundError,
    PermissionDeniedError,
)
from logging_module import logged_step
from repository.db import run_query
from services.audit_log import ACTION_CREATE, record_audit_on
from services.project import fetch_active_membership, fetch_project

from business_logic.calendar import parse_day_of_week
from business_logic.repository import (
    fetch_schedule_record,
    fetch_schedule_records,
    insert_schedule_on,
    resolve_lookup_id,
)


def _not_found_message(schedule_id: int) -> str:
    return f"الگوی جلسه با شناسه {schedule_id} پیدا نشد"


def fetch_schedule(schedule_id: int) -> dict:
    """یک الگو را با شناسه می‌خواند."""
    row = fetch_schedule_record(schedule_id)
    if row is None:
        raise MeetingScheduleNotFoundError(_not_found_message(schedule_id))
    return row


def actor_can_see_schedule(user_id: int, schedule: dict) -> bool:
    """صاحب الگو یا عضو فعال پروژه‌اش می‌تواند ببیند."""
    if schedule["user_id"] == user_id:
        return True
    project_id = schedule.get("project_id")
    if project_id is not None:
        return fetch_active_membership(project_id, user_id) is not None
    return False


def require_schedule_access(user_id: int, schedule_id: int) -> dict:
    """اگر الگو نباشد یا قابل‌مشاهده نباشد خطا می‌دهد."""
    schedule = fetch_schedule(schedule_id)
    if actor_can_see_schedule(user_id, schedule):
        return schedule
    raise PermissionDeniedError("به این الگوی جلسه دسترسی ندارید")


def require_schedule_owner(user_id: int, schedule: dict) -> None:
    """تولید نمونه فقط برای صاحب الگو است."""
    if schedule["user_id"] != user_id:
        raise PermissionDeniedError("فقط صاحب الگو می‌تواند از روی آن جلسه بسازد")


def fetch_schedules(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
    is_active=None,
) -> list:
    """فهرست الگوهای مدیر جاری را می‌خواند."""
    if project_id is not None:
        fetch_project(project_id)
    return fetch_schedule_records(
        user_id,
        limit,
        offset,
        project_id=project_id,
        is_active=is_active,
    )


def insert_schedule(fields: dict, user_id: int) -> int:
    """الگوی تکرار جدید برای مدیر جاری می‌سازد."""
    type_id = resolve_lookup_id(
        "meeting_types",
        fields.get("meeting_type_id"),
        fields.get("meeting_type"),
    )
    try:
        day_of_week = parse_day_of_week(
            fields.get("day_of_week"),
            fields.get("day_name"),
        )
    except ValueError as exc:
        raise InvalidInputError(str(exc)) from exc
    project_id = fields.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
        membership = fetch_active_membership(project_id, user_id)
        if membership is None:
            raise PermissionDeniedError("عضو فعال این پروژه نیستید")
    effective_from = fields.get("effective_from") or date.today()
    payload = {
        "user_id": user_id,
        "project_id": project_id,
        "meeting_type_id": type_id,
        "day_of_week": day_of_week,
        "start_time": fields["start_time"],
        "duration_minutes": fields.get("duration_minutes") or 60,
        "is_active": fields.get("is_active", True),
        "effective_from": effective_from,
        "effective_until": fields.get("effective_until"),
    }

    def work(connection):
        new_id = insert_schedule_on(connection, payload)
        record_audit_on(
            connection,
            user_id,
            ACTION_CREATE,
            "MeetingSchedule",
            new_id,
            None,
            {
                "day_of_week": day_of_week,
                "meeting_type_id": type_id,
                "project_id": project_id,
            },
        )
        return new_id

    return run_query(work)


fetch_schedule = logged_step("fetch")(fetch_schedule)
fetch_schedules = logged_step("fetch")(fetch_schedules)
insert_schedule = logged_step("insert")(insert_schedule)
require_schedule_access = logged_step("auth")(require_schedule_access)
