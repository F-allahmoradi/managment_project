"""سرویس عملیات جدول tasks.

مسئول اگر تعیین شود باید عضو فعال همان پروژه باشد.
فهرست فقط وظایف پروژه‌هایی را برمی‌گرداند که کاربر عضو فعال‌شان است.
عوض کردن وضعیت کار ردیف پیگیری نمی‌سازد.
"""

from errors.crud import InvalidInputError, TaskNotFoundError
from logging_module import logged_step
from repository import (
    as_date,
    delete_row_on,
    disable_task_item_assignee_guard_on,
    fetch_first,
    fetch_task_record,
    fetch_tasks_for_actor_records,
    insert_row_on,
    resolve_lookup_id,
    run_query,
    set_current_user_id_on,
    update_row_on,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, record_audit_on
from services.notification import (
    TYPE_NEW_TASK,
    TYPE_TASK_STATUS,
    insert_notification_on,
)
from repository.soft_delete import task_row_is_cancelled
from services.project import fetch_active_membership, fetch_project
from services.user import fetch_user


def _not_found_message(task_id: int) -> str:
    return f"وظیفه با شناسه {task_id} پیدا نشد"


def _require_active_assignee(project_id: int, user_id: int) -> None:
    """مسئول باید کاربر فعال و عضو فعال همان پروژه باشد."""
    user = fetch_user(user_id)
    if not user["is_active"]:
        raise InvalidInputError("کاربر غیرفعال را نمی‌توان مسئول کار کرد")
    membership = fetch_active_membership(project_id, user_id)
    if membership is None:
        raise InvalidInputError("مسئول باید عضو فعال همین پروژه باشد")


def _resolve_task_lookups(fields: dict) -> dict:
    prepared = {}
    if "status_id" in fields or "status" in fields:
        prepared["status_id"] = resolve_lookup_id(
            "task_statuses",
            fields.get("status_id"),
            fields.get("status"),
        )
    if "priority_id" in fields or "priority" in fields:
        prepared["priority_id"] = resolve_lookup_id(
            "task_priorities",
            fields.get("priority_id"),
            fields.get("priority"),
        )
    if "importance_id" in fields or "importance" in fields:
        prepared["importance_id"] = resolve_lookup_id(
            "task_importances",
            fields.get("importance_id"),
            fields.get("importance"),
        )
    return prepared


def fetch_task(task_id: int) -> dict:
    """یک وظیفه را با شناسه می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_task_record(task_id)
    if row is None or task_row_is_cancelled(row):
        raise TaskNotFoundError(_not_found_message(task_id))
    return row


def fetch_task_project_id(task_id: int) -> int:
    """شناسه پروژهٔ یک وظیفه را برمی‌گرداند."""
    row = fetch_first("tasks", {"id": task_id}, columns=("project_id",))
    if row is None:
        raise TaskNotFoundError(_not_found_message(task_id))
    return row["project_id"]


def fetch_tasks_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """وظایف پروژه‌هایی را می‌خواند که کاربر عضو فعال‌شان است."""
    return fetch_tasks_for_actor_records(user_id, limit, offset, project_id)


def _lookup_name(entity_key: str, lookup_id) -> str:
    row = fetch_first(entity_key, {"id": lookup_id}, columns=("id", "name"))
    if row is None:
        return ""
    return row["name"]


def _task_snapshot(values: dict, lookups: dict) -> dict:
    return {
        "project_id": values.get("project_id"),
        "title": values.get("title"),
        "assigned_to_user_id": values.get("assigned_to_user_id"),
        "status": _lookup_name("task_statuses", lookups.get("status_id")),
        "priority": _lookup_name("task_priorities", lookups.get("priority_id")),
        "importance": _lookup_name("task_importances", lookups.get("importance_id")),
        "due_date": values.get("due_date"),
    }


def insert_task(fields: dict, created_by: int) -> int:
    """یک وظیفه را درج می‌کند و برای مسئول اعلان و ممیزی می‌نویسد."""
    project_id = fields["project_id"]
    fetch_project(project_id)
    lookups = _resolve_task_lookups(fields)
    assigned_to = fields.get("assigned_to_user_id")
    if assigned_to is not None:
        _require_active_assignee(project_id, assigned_to)
    start_date = as_date(fields.get("start_date"))
    due_date = as_date(fields.get("due_date"))
    if start_date is not None and due_date is not None and due_date < start_date:
        raise InvalidInputError("مهلت نباید قبل از تاریخ شروع باشد")
    values = {
        "project_id": project_id,
        "title": fields["title"],
        "description": fields.get("description"),
        "assigned_to_user_id": assigned_to,
        "created_by_user_id": created_by,
        "status_id": lookups["status_id"],
        "priority_id": lookups["priority_id"],
        "importance_id": lookups["importance_id"],
        "importance_percent": fields.get("importance_percent"),
        "start_date": fields.get("start_date"),
        "due_date": fields.get("due_date"),
    }
    snapshot = _task_snapshot(values, lookups)

    def work(connection):
        task_id = insert_row_on(connection, "tasks", values)
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Task",
            task_id,
            None,
            snapshot,
        )
        if assigned_to is not None:
            insert_notification_on(
                connection,
                assigned_to,
                TYPE_NEW_TASK,
                f"وظیفه {fields['title']} به تو اختصاص داده شد.",
            )
        return task_id

    return run_query(work, unique_messages_for("tasks"))


def update_task(fields: dict, actor_id=None) -> int:
    """یک وظیفه موجود را به‌روز می‌کند؛ ردیف پیگیری ساخته نمی‌شود."""
    task_id = fields.get("id")
    if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id < 1:
        raise InvalidInputError("شناسه وظیفه نامعتبر است")
    existing = fetch_task(task_id)
    prepared = {"id": task_id}
    for key in (
        "title",
        "description",
        "importance_percent",
        "start_date",
        "due_date",
        "completed_at",
    ):
        if key in fields:
            prepared[key] = fields[key]
    if "assigned_to_user_id" in fields:
        assigned_to = fields["assigned_to_user_id"]
        _require_active_assignee(existing["project_id"], assigned_to)
        prepared["assigned_to_user_id"] = assigned_to
    prepared.update(_resolve_task_lookups(fields))
    if len(prepared) == 1:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    start_date = as_date(prepared.get("start_date", existing["start_date"]))
    due_date = as_date(prepared.get("due_date", existing["due_date"]))
    if start_date is not None and due_date is not None and due_date < start_date:
        raise InvalidInputError("مهلت نباید قبل از تاریخ شروع باشد")
    old_value = {}
    new_value = {}
    title = prepared.get("title", existing["title"])
    if "title" in prepared and prepared["title"] != existing["title"]:
        old_value["title"] = existing["title"]
        new_value["title"] = prepared["title"]
    if "assigned_to_user_id" in prepared:
        if prepared["assigned_to_user_id"] != existing["assigned_to_user_id"]:
            old_value["assigned_to_user_id"] = existing["assigned_to_user_id"]
            new_value["assigned_to_user_id"] = prepared["assigned_to_user_id"]
    if "status_id" in prepared and prepared["status_id"] != existing["status_id"]:
        old_value["status"] = existing["status_name"]
        new_value["status"] = _lookup_name("task_statuses", prepared["status_id"])
    assignee_changed = "assigned_to_user_id" in new_value
    status_changed = "status" in new_value
    new_assignee = prepared.get("assigned_to_user_id", existing["assigned_to_user_id"])

    def work(connection):
        updated_id = update_row_on(
            connection,
            "tasks",
            prepared,
            TaskNotFoundError,
            _not_found_message(task_id),
        )
        if old_value or new_value:
            record_audit_on(
                connection,
                actor_id,
                ACTION_UPDATE,
                "Task",
                updated_id,
                old_value or None,
                new_value or None,
            )
        else:
            record_audit_on(
                connection,
                actor_id,
                ACTION_UPDATE,
                "Task",
                updated_id,
                None,
                {key: prepared[key] for key in prepared if key != "id"},
            )
        if assignee_changed and new_assignee is not None:
            insert_notification_on(
                connection,
                new_assignee,
                TYPE_NEW_TASK,
                f"وظیفه {title} به تو اختصاص داده شد.",
            )
        if status_changed and new_assignee is not None and not assignee_changed:
            insert_notification_on(
                connection,
                new_assignee,
                TYPE_TASK_STATUS,
                (
                    f"وضعیت وظیفه {title} از «{old_value['status']}» "
                    f"به «{new_value['status']}» تغییر کرد."
                ),
            )
        return updated_id

    return run_query(work, unique_messages_for("tasks"))


def delete_task(task_id: int, actor_id: int) -> int:
    """وظیفه را لغو می‌کند (وضعیت «لغو شده»)؛ ردیف در DB می‌ماند."""
    existing = fetch_task_record(task_id)
    if existing is None:
        raise TaskNotFoundError(_not_found_message(task_id))
    if task_row_is_cancelled(existing):
        return task_id

    def work(connection):
        set_current_user_id_on(connection, actor_id)
        disable_task_item_assignee_guard_on(connection)
        deleted_id = delete_row_on(
            connection,
            "tasks",
            task_id,
            TaskNotFoundError,
            _not_found_message(task_id),
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_DELETE,
            "Task",
            deleted_id,
            {
                "title": existing.get("title"),
                "project_id": existing.get("project_id"),
            },
            None,
        )
        return deleted_id

    return run_query(work, unique_messages_for("tasks"))


insert_task = logged_step("insert")(insert_task)
fetch_task = logged_step("fetch")(fetch_task)
fetch_task_project_id = logged_step("fetch")(fetch_task_project_id)
fetch_tasks_for_actor = logged_step("fetch")(fetch_tasks_for_actor)
update_task = logged_step("update")(update_task)
delete_task = logged_step("delete")(delete_task)
