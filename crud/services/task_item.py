"""سرویس جدول task_items: زیرکار و تیک داخل یک Task.

فقط مسئول همان وظیفه می‌تواند بسازد، ویرایش کند، تیک بزند یا حذف کند.
هویت روی سشن با SET LOCAL app.current_user_id گذاشته می‌شود.
یادآوری از تاریخ زیرکار ساخته نمی‌شود.
"""

from errors.crud import (
    InvalidInputError,
    PermissionDeniedError,
    TaskItemNotFoundError,
)
from logging_module import logged_step
from repository import (
    as_date,
    fetch_first,
    fetch_next_task_item_sort_order,
    fetch_task_item_project_id_record,
    fetch_task_item_record,
    fetch_task_items_for_task_records,
    insert_row_on,
    run_query,
    set_current_user_id_on,
    update_row_on,
)
from repository.columns import unique_messages_for
from services.audit_log import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_UPDATE,
    record_audit_on,
)
from services.task import fetch_task


def _not_found_message(item_id: int) -> str:
    return f"زیرکار با شناسه {item_id} پیدا نشد"


def _require_task_assignee(task: dict, actor_id: int) -> None:
    """فقط assigned_to_user_id همان Task اجازه تغییر زیرکار دارد."""
    assignee = task.get("assigned_to_user_id")
    if assignee is None:
        raise PermissionDeniedError(
            "این وظیفه مسئول ندارد؛ فقط مسئول می‌تواند زیرکار را تغییر دهد"
        )
    if assignee != actor_id:
        raise PermissionDeniedError(
            "فقط مسئول همین وظیفه می‌تواند زیرکار را تغییر دهد"
        )


def _validate_item_dates(start_date, end_date) -> None:
    start = as_date(start_date)
    end = as_date(end_date)
    if start is not None and end is not None and end < start:
        raise InvalidInputError("پایان زیرکار نباید قبل از شروع باشد")


def _as_tree(rows: list) -> list:
    """فهرست تخت را به درخت children بر اساس parent_item_id تبدیل می‌کند."""
    by_id = {row["id"]: {**row, "children": []} for row in rows}
    roots = []
    for row in rows:
        node = by_id[row["id"]]
        parent_id = row["parent_item_id"]
        if parent_id is None or parent_id not in by_id:
            roots.append(node)
        else:
            by_id[parent_id]["children"].append(node)
    return roots


def fetch_task_item(item_id: int) -> dict:
    """یک زیرکار را با شناسه می‌خواند."""
    row = fetch_task_item_record(item_id)
    if row is None:
        raise TaskItemNotFoundError(_not_found_message(item_id))
    return row


def fetch_task_item_project_id(item_id: int) -> int:
    """شناسه پروژهٔ وظیفهٔ یک زیرکار را برمی‌گرداند."""
    row = fetch_task_item_project_id_record(item_id)
    if row is None:
        raise TaskItemNotFoundError(_not_found_message(item_id))
    return row["project_id"]


def fetch_task_items(task_id: int) -> dict:
    """زیرکارهای یک وظیفه را تخت و درختی، با ترتیب sort_order، برمی‌گرداند."""
    fetch_task(task_id)
    records = fetch_task_items_for_task_records(task_id)
    return {"records": records, "tree": _as_tree(records)}


def _resolve_parent(task_id: int, parent_item_id) -> None:
    if parent_item_id is None:
        return
    parent = fetch_first("task_items", {"id": parent_item_id}, columns=("id", "task_id"))
    if parent is None:
        raise InvalidInputError("زیرکار والد پیدا نشد")
    if parent["task_id"] != task_id:
        raise InvalidInputError("زیرکار والد باید مال همین وظیفه باشد")


def insert_task_item(fields: dict, actor_id: int) -> int:
    """یک زیرکار سطح اول یا تو در تو درج می‌کند؛ یادآوری نمی‌سازد."""
    task_id = fields["task_id"]
    task = fetch_task(task_id)
    _require_task_assignee(task, actor_id)
    parent_item_id = fields.get("parent_item_id")
    _resolve_parent(task_id, parent_item_id)
    _validate_item_dates(fields.get("start_date"), fields.get("end_date"))
    sort_order = fields.get("sort_order")
    if sort_order is None:
        sort_order = fetch_next_task_item_sort_order(task_id, parent_item_id)
    values = {
        "task_id": task_id,
        "parent_item_id": parent_item_id,
        "title": fields["title"],
        "description": fields.get("description"),
        "sort_order": sort_order,
        "start_date": fields.get("start_date"),
        "end_date": fields.get("end_date"),
        "created_by_user_id": actor_id,
    }

    def work(connection):
        set_current_user_id_on(connection, actor_id)
        item_id = insert_row_on(connection, "task_items", values)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "TaskItem",
            item_id,
            None,
            {
                "task_id": task_id,
                "parent_item_id": parent_item_id,
                "title": fields["title"],
                "sort_order": sort_order,
            },
        )
        return item_id

    return run_query(work, unique_messages_for("task_items"))


def update_task_item(fields: dict, actor_id: int) -> int:
    """عنوان، ترتیب یا تاریخ یک زیرکار را به‌روز می‌کند؛ تیک نیست."""
    item_id = fields.get("id")
    if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id < 1:
        raise InvalidInputError("شناسه زیرکار نامعتبر است")
    existing = fetch_task_item(item_id)
    task = fetch_task(existing["task_id"])
    _require_task_assignee(task, actor_id)
    prepared = {"id": item_id}
    for key in ("title", "description", "sort_order", "start_date", "end_date"):
        if key in fields:
            prepared[key] = fields[key]
    if len(prepared) == 1:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    start_date = prepared.get("start_date", existing["start_date"])
    end_date = prepared.get("end_date", existing["end_date"])
    _validate_item_dates(start_date, end_date)
    new_value = {key: prepared[key] for key in prepared if key != "id"}
    old_value = {key: existing.get(key) for key in new_value if key in existing}

    def work(connection):
        set_current_user_id_on(connection, actor_id)
        updated_id = update_row_on(
            connection,
            "task_items",
            prepared,
            TaskItemNotFoundError,
            _not_found_message(item_id),
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "TaskItem",
            updated_id,
            old_value,
            new_value,
        )
        return updated_id

    return run_query(work, unique_messages_for("task_items"))


def complete_task_item(item_id: int, actor_id: int, is_completed: bool = True) -> int:
    """زیرکار را تیک می‌زند یا تیک را برمی‌دارد."""
    existing = fetch_task_item(item_id)
    task = fetch_task(existing["task_id"])
    _require_task_assignee(task, actor_id)
    prepared = {"id": item_id, "is_completed": is_completed}
    if is_completed:
        prepared["completed_by_user_id"] = actor_id
    else:
        prepared["completed_at"] = None
        prepared["completed_by_user_id"] = None

    def work(connection):
        set_current_user_id_on(connection, actor_id)
        updated_id = update_row_on(
            connection,
            "task_items",
            prepared,
            TaskItemNotFoundError,
            _not_found_message(item_id),
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "TaskItem",
            updated_id,
            {"is_completed": existing["is_completed"]},
            {"is_completed": is_completed},
        )
        return updated_id

    return run_query(work, unique_messages_for("task_items"))


def _soft_delete_task_item_tree_on(connection, item_id: int) -> None:
    """زیرکار و همهٔ فرزندانش را غیرفعال می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH RECURSIVE sub AS (
                SELECT id FROM task_items WHERE id = %s AND is_active = true
                UNION ALL
                SELECT i.id
                FROM task_items i
                JOIN sub ON i.parent_item_id = sub.id
                WHERE i.is_active = true
            )
            UPDATE task_items SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id IN (SELECT id FROM sub)
            """,
            [item_id],
        )
        if cursor.rowcount < 1:
            raise TaskItemNotFoundError(_not_found_message(item_id))


def delete_task_item(item_id: int, actor_id: int) -> int:
    """زیرکار را غیرفعال می‌کند؛ فرزندان هم is_active=false می‌شوند."""
    existing = fetch_task_item(item_id)
    task = fetch_task(existing["task_id"])
    _require_task_assignee(task, actor_id)

    def work(connection):
        set_current_user_id_on(connection, actor_id)
        _soft_delete_task_item_tree_on(connection, item_id)
        record_audit_on(
            connection,
            actor_id,
            ACTION_DELETE,
            "TaskItem",
            item_id,
            {"title": existing["title"], "task_id": existing["task_id"]},
            {"is_active": False},
        )
        return item_id

    return run_query(work, unique_messages_for("task_items"))


fetch_task_item = logged_step("fetch")(fetch_task_item)
fetch_task_item_project_id = logged_step("fetch")(fetch_task_item_project_id)
fetch_task_items = logged_step("fetch")(fetch_task_items)
insert_task_item = logged_step("insert")(insert_task_item)
update_task_item = logged_step("update")(update_task_item)
complete_task_item = logged_step("update")(complete_task_item)
delete_task_item = logged_step("delete")(delete_task_item)
