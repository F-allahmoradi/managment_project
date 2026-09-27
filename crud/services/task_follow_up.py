"""سرویس عملیات جدول task_follow_ups.

هر ردیف یک پیگیری جدا روی همان وظیفه است. ساخت یا ویرایش وظیفه
اینجا ردیفی درج نمی‌کند.
"""

from errors.crud import InvalidInputError, TaskFollowUpNotFoundError
from logging_module import logged_step
from repository import (
    count_follow_ups_for_task,
    fetch_follow_up_project_id_record,
    fetch_follow_up_record,
    fetch_follow_ups_for_task_records,
    insert_row,
    resolve_lookup_id,
)
from services.audit_log import ACTION_CREATE, record_audit
from services.task import fetch_task


def _not_found_message(follow_up_id: int) -> str:
    return f"پیگیری با شناسه {follow_up_id} پیدا نشد"


def fetch_task_follow_up(follow_up_id: int) -> dict:
    """یک پیگیری را با شناسه می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_follow_up_record(follow_up_id)
    if row is None:
        raise TaskFollowUpNotFoundError(_not_found_message(follow_up_id))
    return row


def fetch_task_follow_up_project_id(follow_up_id: int) -> int:
    """شناسه پروژهٔ وظیفهٔ یک پیگیری را برمی‌گرداند."""
    row = fetch_follow_up_project_id_record(follow_up_id)
    if row is None:
        raise TaskFollowUpNotFoundError(_not_found_message(follow_up_id))
    return row["project_id"]


def fetch_task_follow_ups(task_id: int, limit: int, offset: int) -> list:
    """پیگیری‌های یک وظیفه را با صفحه‌بندی می‌خواند."""
    fetch_task(task_id)
    return fetch_follow_ups_for_task_records(task_id, limit, offset)


def count_task_follow_ups(task_id: int) -> int:
    """تعداد پیگیری‌های یک وظیفه را برمی‌گرداند."""
    return count_follow_ups_for_task(task_id)


def insert_task_follow_up(fields: dict, followed_by: int) -> int:
    """یک پیگیری روی وظیفه درج می‌کند؛ وضعیت خود کار عوض نمی‌شود."""
    task_id = fields["task_id"]
    fetch_task(task_id)
    note = fields.get("note")
    if not note or not str(note).strip():
        raise InvalidInputError("متن پیگیری لازم است")
    payload = {
        "task_id": task_id,
        "followed_by_user_id": followed_by,
        "follow_up_type_id": resolve_lookup_id(
            "follow_up_types",
            fields.get("follow_up_type_id"),
            fields.get("follow_up_type"),
        ),
        "status_id": resolve_lookup_id(
            "task_follow_up_statuses",
            fields.get("status_id"),
            fields.get("status"),
        ),
        "note": note,
        "follow_up_date": fields.get("follow_up_date"),
        "next_follow_up_date": fields.get("next_follow_up_date"),
    }
    new_id = insert_row("task_follow_ups", payload)
    record_audit(
        followed_by,
        ACTION_CREATE,
        "TaskFollowUp",
        new_id,
        None,
        {"task_id": task_id, "note": note},
    )
    return new_id


insert_task_follow_up = logged_step("insert")(insert_task_follow_up)
fetch_task_follow_up = logged_step("fetch")(fetch_task_follow_up)
fetch_task_follow_up_project_id = logged_step("fetch")(
    fetch_task_follow_up_project_id
)
fetch_task_follow_ups = logged_step("fetch")(fetch_task_follow_ups)
count_task_follow_ups = logged_step("fetch")(count_task_follow_ups)
