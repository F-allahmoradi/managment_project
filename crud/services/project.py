"""سرویس عملیات جدول projects.

سازنده هنگام درج به‌عنوان عضو با نقش «مدیر پروژه» وارد
project_members می‌شود. فهرست فقط پروژه‌هایی را برمی‌گرداند
که کاربر جاری عضو فعال‌شان است.
"""

from auth.permissions import is_director
from errors.crud import InvalidInputError, ProjectNotFoundError
from logging_module import logged_step
from repository import (
    as_date,
    delete_row_on,
    fetch_active_membership_record,
    fetch_first,
    fetch_project_record,
    fetch_projects_for_actor_records,
    insert_row_on,
    resolve_lookup_id,
    run_query,
    update_row,
)
from repository.columns import unique_messages_for
from repository.soft_delete import project_row_is_cancelled
from services.audit_log import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_UPDATE,
    record_audit,
    record_audit_on,
)

CREATOR_PROJECT_ROLE_NAME = "مدیر پروژه"


def _not_found_message(project_id: int) -> str:
    return f"پروژه با شناسه {project_id} پیدا نشد"


def fetch_project(project_id: int) -> dict:
    """یک پروژه را با شناسه می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_project_record(project_id)
    if row is None or project_row_is_cancelled(row):
        raise ProjectNotFoundError(_not_found_message(project_id))
    return row


def project_exists(project_id: int) -> bool:
    """اگر ردیف projects وجود داشته باشد True است."""
    return fetch_first("projects", {"id": project_id}, columns=("id",)) is not None


def fetch_active_membership(project_id: int, user_id: int):
    """عضویت فعال کاربر در پروژه را برمی‌گرداند یا None."""
    return fetch_active_membership_record(project_id, user_id)


def fetch_projects_for_actor(user_id: int, limit: int, offset: int) -> list:
    """مدیر کل همهٔ پروژه‌ها را می‌بیند؛ بقیه فقط عضویت فعال."""
    return fetch_projects_for_actor_records(
        user_id,
        limit,
        offset,
        unrestricted=is_director(user_id),
    )


def _resolve_type_and_status(fields: dict) -> tuple[int, int]:
    type_id = resolve_lookup_id(
        "project_types",
        fields.get("project_type_id"),
        fields.get("project_type"),
    )
    status_id = resolve_lookup_id(
        "project_statuses",
        fields.get("project_status_id"),
        fields.get("project_status"),
    )
    return type_id, status_id


def insert_project(fields: dict, created_by: int) -> int:
    """پروژه را درج می‌کند و سازنده را مدیر همان پروژه می‌کند."""
    type_id, status_id = _resolve_type_and_status(fields)
    manager_role = fetch_first(
        "project_roles",
        {"name": CREATOR_PROJECT_ROLE_NAME, "is_active": True},
        columns=("id",),
    )
    if manager_role is None:
        raise InvalidInputError(
            f"نقش داخل پروژه «{CREATOR_PROJECT_ROLE_NAME}» در seed نیست"
        )
    values = {
        "name": fields["name"],
        "description": fields.get("description"),
        "project_type_id": type_id,
        "project_status_id": status_id,
        "start_date": fields.get("start_date"),
        "end_date": fields.get("end_date"),
        "created_by": created_by,
    }

    def work(connection):
        project_id = insert_row_on(connection, "projects", values)
        insert_row_on(
            connection,
            "project_members",
            {
                "project_id": project_id,
                "user_id": created_by,
                "project_role_id": manager_role["id"],
                "is_active": True,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Project",
            project_id,
            None,
            {
                "name": values["name"],
                "project_type_id": type_id,
                "project_status_id": status_id,
            },
        )
        return project_id

    return run_query(work, unique_messages_for("project_members"))


def update_project(fields: dict, actor_id=None) -> int:
    """یک پروژه موجود را به‌روز می‌کند؛ created_by عوض نمی‌شود."""
    project_id = fields.get("id")
    if not isinstance(project_id, int) or isinstance(project_id, bool) or project_id < 1:
        raise InvalidInputError("شناسه پروژه نامعتبر است")
    existing = fetch_project(project_id)
    prepared = {"id": project_id}
    for key in ("name", "description", "start_date", "end_date"):
        if key in fields:
            prepared[key] = fields[key]
    if "project_type_id" in fields or "project_type" in fields:
        prepared["project_type_id"] = resolve_lookup_id(
            "project_types",
            fields.get("project_type_id"),
            fields.get("project_type"),
        )
    if "project_status_id" in fields or "project_status" in fields:
        prepared["project_status_id"] = resolve_lookup_id(
            "project_statuses",
            fields.get("project_status_id"),
            fields.get("project_status"),
        )
    if len(prepared) == 1:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    start_date = as_date(prepared.get("start_date", existing["start_date"]))
    end_date = as_date(prepared.get("end_date", existing["end_date"]))
    if start_date is not None and end_date is not None and end_date < start_date:
        raise InvalidInputError("تاریخ پایان نباید قبل از تاریخ شروع باشد")
    updated_id = update_row(
        "projects",
        prepared,
        ProjectNotFoundError,
        _not_found_message(project_id),
    )
    new_value = {key: prepared[key] for key in prepared if key != "id"}
    old_value = {key: existing.get(key) for key in new_value if key in existing}
    record_audit(actor_id, ACTION_UPDATE, "Project", updated_id, old_value, new_value)
    return updated_id


def delete_project(project_id: int, actor_id: int) -> int:
    """پروژه را لغو می‌کند (وضعیت «لغو شده»)؛ هیچ ردیفی DELETE نمی‌شود."""
    existing = fetch_project_record(project_id)
    if existing is None:
        raise ProjectNotFoundError(_not_found_message(project_id))
    if project_row_is_cancelled(existing):
        return project_id

    def work(connection):
        deleted_id = delete_row_on(
            connection,
            "projects",
            project_id,
            ProjectNotFoundError,
            _not_found_message(project_id),
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_DELETE,
            "Project",
            deleted_id,
            {"name": existing.get("name")},
            None,
        )
        return deleted_id

    return run_query(work, unique_messages_for("projects"))


insert_project = logged_step("insert")(insert_project)
fetch_project = logged_step("fetch")(fetch_project)
fetch_projects_for_actor = logged_step("fetch")(fetch_projects_for_actor)
update_project = logged_step("update")(update_project)
delete_project = logged_step("delete")(delete_project)
fetch_active_membership = logged_step("fetch")(fetch_active_membership)
resolve_lookup_id = logged_step("lookup")(resolve_lookup_id)
