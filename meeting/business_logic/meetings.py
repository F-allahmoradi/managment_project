"""دامنهٔ نمونهٔ جلسه: ساخت، فهرست، خواندن، لغو.

ضبط و همگام‌سازی در record و sync جدا هستند.
تداخل ساعت در کد بررسی می‌شود.
"""

from datetime import timedelta

from errors.crud import (
    InvalidInputError,
    MeetingNotFoundError,
    MeetingSlotConflictError,
    PermissionDeniedError,
)
from logging_module import logged_step
from repository.db import json_safe, run_query
from services.audit_log import ACTION_CREATE, ACTION_UPDATE, record_audit_on
from services.project import fetch_active_membership, fetch_project

from business_logic.calendar import isoformat_naive, shift_weeks
from business_logic.repository import (
    cancel_meeting_on,
    fetch_cancelled_status_id,
    fetch_meeting_record,
    fetch_meetings_for_actor_records,
    fetch_overlapping_meeting,
    fetch_participant_records,
    fetch_planned_status_id,
    fetch_sync_item_records,
    insert_meeting_on,
    meeting_has_user_participant,
    resolve_lookup_id,
    update_meeting_on,
)
from business_logic.schedules import fetch_schedule


def _not_found_message(meeting_id: int) -> str:
    return f"جلسه با شناسه {meeting_id} پیدا نشد"


def fetch_meeting(meeting_id: int) -> dict:
    """یک جلسه را با شناسه می‌خواند."""
    row = fetch_meeting_record(meeting_id)
    if row is None:
        raise MeetingNotFoundError(_not_found_message(meeting_id))
    return row


def actor_can_see_meeting(user_id: int, meeting: dict) -> bool:
    """مدیر، شرکت‌کنندهٔ کاربر، یا عضو پروژهٔ جلسهٔ PROJECT می‌تواند ببیند."""
    if meeting["manager_user_id"] == user_id:
        return True
    if meeting_has_user_participant(meeting["id"], user_id):
        return True
    if meeting.get("visibility") == "PROJECT" and meeting.get("project_id") is not None:
        return fetch_active_membership(meeting["project_id"], user_id) is not None
    return False


def require_meeting_access(user_id: int, meeting_id: int) -> dict:
    """اگر جلسه نباشد یا قابل‌مشاهده نباشد خطا می‌دهد."""
    meeting = fetch_meeting(meeting_id)
    if actor_can_see_meeting(user_id, meeting):
        return meeting
    raise PermissionDeniedError("به این جلسه دسترسی ندارید")


def require_meeting_manager(user_id: int, meeting: dict) -> None:
    """لغو و افزودن شرکت‌کننده فقط برای مدیر جلسه است."""
    if meeting["manager_user_id"] != user_id:
        raise PermissionDeniedError("فقط مدیر جلسه می‌تواند این کار را بکند")


def fetch_meetings(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
    status_id=None,
    status=None,
) -> list:
    """جلسات قابل‌مشاهدهٔ کاربر جاری را می‌خواند."""
    if project_id is not None:
        fetch_project(project_id)
    resolved_status = status_id
    if resolved_status is None and status:
        resolved_status = resolve_lookup_id("meeting_statuses", None, status)
    return fetch_meetings_for_actor_records(
        user_id,
        limit,
        offset,
        project_id=project_id,
        status_id=resolved_status,
    )


def meeting_with_participants(meeting: dict) -> dict:
    """شرکت‌کنندگان و خروجی‌های sync را به دیکشنری جلسه می‌چسباند."""
    payload = dict(meeting)
    payload["participants"] = fetch_participant_records(meeting["id"])
    payload["sync_items"] = fetch_sync_item_records(meeting["id"])
    return payload


def scheduled_end(scheduled_at, duration_minutes: int):
    """پایان برنامه‌ریزی‌شده را از شروع و مدت می‌سازد."""
    return scheduled_at + timedelta(minutes=duration_minutes)


def suggest_after_conflict(scheduled_at, duration_minutes: int) -> dict:
    """هفتهٔ بعد همان روز و ساعت را برای پیشنهاد برمی‌گرداند."""
    nxt, nxt_end = shift_weeks(scheduled_at, duration_minutes, weeks=1)
    return {
        "requested_at": isoformat_naive(scheduled_at),
        "suggested_at": isoformat_naive(nxt),
        "suggested_end_at": isoformat_naive(nxt_end),
    }


def find_slot_conflict(
    manager_user_id: int,
    scheduled_at,
    scheduled_end_at,
    exclude_meeting_id=None,
):
    """جلسهٔ متداخل غیرلغو شده را برمی‌گرداند یا None."""
    cancelled_id = fetch_cancelled_status_id()
    return fetch_overlapping_meeting(
        manager_user_id,
        scheduled_at,
        scheduled_end_at,
        cancelled_id,
        exclude_meeting_id=exclude_meeting_id,
    )


def raise_if_conflict(
    manager_user_id: int,
    scheduled_at,
    duration_minutes: int,
    exclude_meeting_id=None,
) -> None:
    """اگر بازه پر باشد خطای تداخل با پیشنهاد هفتهٔ بعد می‌دهد."""
    end_at = scheduled_end(scheduled_at, duration_minutes)
    conflict = find_slot_conflict(
        manager_user_id,
        scheduled_at,
        end_at,
        exclude_meeting_id=exclude_meeting_id,
    )
    if conflict is None:
        return
    suggestion = suggest_after_conflict(scheduled_at, duration_minutes)
    raise MeetingSlotConflictError(
        "این ساعت پر است؛ هفتهٔ بعد پیشنهاد می‌شود",
        requested_at=suggestion["requested_at"],
        suggested_at=suggestion["suggested_at"],
    )


def resolve_visibility(fields: dict, project_id) -> str:
    """visibility را با قانون PROJECT بدون پروژه رد می‌کند."""
    visibility = (fields.get("visibility") or "PRIVATE").upper()
    if visibility == "PROJECT" and project_id is None:
        raise InvalidInputError("visibility برابر PROJECT بدون پروژه مجاز نیست")
    return visibility


def insert_meeting(fields: dict, manager_user_id: int) -> int:
    """یک جلسهٔ برنامه‌ریزی‌شده می‌سازد؛ ضبط و sync نوشته نمی‌شود."""
    type_id = resolve_lookup_id(
        "meeting_types",
        fields.get("meeting_type_id"),
        fields.get("meeting_type"),
    )
    project_id = fields.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
        membership = fetch_active_membership(project_id, manager_user_id)
        if membership is None:
            raise PermissionDeniedError("عضو فعال این پروژه نیستید")
    schedule_id = fields.get("schedule_id")
    if schedule_id is not None:
        schedule = fetch_schedule(schedule_id)
        if schedule["user_id"] != manager_user_id:
            raise PermissionDeniedError("این الگو مال شما نیست")
    visibility = resolve_visibility(fields, project_id)
    duration = fields.get("duration_minutes") or 60
    scheduled_at = fields["scheduled_at"]
    if hasattr(scheduled_at, "tzinfo") and scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.replace(tzinfo=None)
    raise_if_conflict(manager_user_id, scheduled_at, duration)
    status_id = fetch_planned_status_id()
    payload = {
        "project_id": project_id,
        "manager_user_id": manager_user_id,
        "schedule_id": schedule_id,
        "meeting_type_id": type_id,
        "status_id": status_id,
        "visibility": visibility,
        "title": fields["title"],
        "scheduled_at": scheduled_at,
        "scheduled_end_at": scheduled_end(scheduled_at, duration),
        "duration_minutes": duration,
        "location": fields.get("location"),
    }

    def work(connection):
        new_id = insert_meeting_on(connection, payload)
        record_audit_on(
            connection,
            manager_user_id,
            ACTION_CREATE,
            "Meeting",
            new_id,
            None,
            {
                "title": payload["title"],
                "scheduled_at": json_safe(scheduled_at),
                "visibility": visibility,
                "project_id": project_id,
            },
        )
        return new_id

    return run_query(work)


def update_meeting(fields: dict, actor_id: int) -> int:
    """جلسهٔ مدیر جاری را به‌روز می‌کند؛ لغو شده ویرایش نمی‌شود."""
    meeting_id = fields["id"]
    meeting = require_meeting_access(actor_id, meeting_id)
    require_meeting_manager(actor_id, meeting)
    if meeting["status_name"] == "لغو شده":
        raise InvalidInputError("جلسه لغو شده ویرایش نمی‌شود")
    project_id = fields["project_id"] if "project_id" in fields else meeting.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
        membership = fetch_active_membership(project_id, actor_id)
        if membership is None:
            raise PermissionDeniedError("عضو فعال این پروژه نیستید")
    visibility = fields.get("visibility") or meeting["visibility"]
    visibility = resolve_visibility({"visibility": visibility}, project_id)
    if "meeting_type_id" in fields or "meeting_type" in fields:
        type_id = resolve_lookup_id(
            "meeting_types",
            fields.get("meeting_type_id"),
            fields.get("meeting_type"),
        )
    else:
        type_id = meeting["meeting_type_id"]
    title = fields.get("title") or meeting["title"]
    duration = fields.get("duration_minutes") or meeting["duration_minutes"]
    scheduled_at = fields.get("scheduled_at", meeting["scheduled_at"])
    if hasattr(scheduled_at, "tzinfo") and scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.replace(tzinfo=None)
    location = fields["location"] if "location" in fields else meeting.get("location")
    raise_if_conflict(
        actor_id,
        scheduled_at,
        duration,
        exclude_meeting_id=meeting_id,
    )
    payload = {
        "project_id": project_id,
        "meeting_type_id": type_id,
        "visibility": visibility,
        "title": title,
        "scheduled_at": scheduled_at,
        "scheduled_end_at": scheduled_end(scheduled_at, duration),
        "duration_minutes": duration,
        "location": location,
    }

    def work(connection):
        updated = update_meeting_on(connection, meeting_id, payload)
        if updated is None:
            raise MeetingNotFoundError(_not_found_message(meeting_id))
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "Meeting",
            meeting_id,
            {
                "title": meeting["title"],
                "scheduled_at": json_safe(meeting["scheduled_at"]),
            },
            {
                "title": payload["title"],
                "scheduled_at": json_safe(scheduled_at),
            },
        )
        return updated

    return run_query(work)


def cancel_meeting(meeting_id: int, actor_id: int) -> int:
    """جلسهٔ برنامه‌ریزی‌شده را لغو می‌کند؛ ردیف حذف نمی‌شود."""
    meeting = require_meeting_access(actor_id, meeting_id)
    require_meeting_manager(actor_id, meeting)
    if meeting["status_name"] == "لغو شده":
        raise InvalidInputError("این جلسه از قبل لغو شده")
    if meeting["status_name"] != "برنامه‌ریزی شده":
        raise InvalidInputError("فقط جلسهٔ برنامه‌ریزی‌شده لغو می‌شود")
    cancelled_id = fetch_cancelled_status_id()

    def work(connection):
        updated = cancel_meeting_on(connection, meeting_id, cancelled_id)
        if updated is None:
            raise MeetingNotFoundError(_not_found_message(meeting_id))
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "Meeting",
            meeting_id,
            {"status_name": meeting["status_name"]},
            {"status_name": "لغو شده"},
        )
        return updated

    return run_query(work)


fetch_meeting = logged_step("fetch")(fetch_meeting)
fetch_meetings = logged_step("fetch")(fetch_meetings)
insert_meeting = logged_step("insert")(insert_meeting)
update_meeting = logged_step("update")(update_meeting)
cancel_meeting = logged_step("update")(cancel_meeting)
require_meeting_access = logged_step("auth")(require_meeting_access)
find_slot_conflict = logged_step("calculate")(find_slot_conflict)
