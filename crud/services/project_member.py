"""سرویس عملیات جدول project_members.

نقش اینجا نقش داخل پروژه است، نه نقش سراسری roles.
افزودن عضو برای عضو جدید اعلان «افزوده شدن به پروژه» می‌سازد.
"""

from errors.crud import (
    InvalidInputError,
    ProjectMemberNotFoundError,
    ProjectNotFoundError,
)
from logging_module import logged_step
from repository import (
    fetch_first,
    fetch_member_record,
    fetch_members_for_project_records,
    insert_row,
    insert_row_on,
    resolve_lookup_id,
    run_query,
    update_row,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, ACTION_UPDATE, record_audit, record_audit_on
from services.notification import TYPE_ADDED_TO_PROJECT, insert_notification_on
from services.project import fetch_project, project_exists
from services.user import fetch_user


def _not_found_message(row_id: int) -> str:
    return f"عضویت با شناسه {row_id} پیدا نشد"


def fetch_project_member(row_id: int) -> dict:
    """یک ردیف عضویت را با شناسه می‌خواند."""
    row = fetch_member_record(row_id)
    if row is None:
        raise ProjectMemberNotFoundError(_not_found_message(row_id))
    return row


def fetch_project_members(project_id: int, limit: int, offset: int) -> list:
    """اعضای یک پروژه را با صفحه‌بندی می‌خواند."""
    if not project_exists(project_id):
        raise ProjectNotFoundError(f"پروژه با شناسه {project_id} پیدا نشد")
    return fetch_members_for_project_records(project_id, limit, offset)


def ensure_project_role(name: str) -> int:
    """نقش داخل پروژه را با نام پیدا می‌کند و اگر نباشد می‌سازد."""
    cleaned = str(name or "").strip()
    if not cleaned:
        raise InvalidInputError("نقش داخل پروژه لازم است")
    if len(cleaned) > 100:
        raise InvalidInputError("نام نقش داخل پروژه بلندتر از ۱۰۰ نویسه است")
    existing = fetch_first("project_roles", {"name": cleaned}, columns=("id", "is_active"))
    if existing is not None:
        if existing.get("is_active") is False:
            raise InvalidInputError(f"نقش داخل پروژه «{cleaned}» غیرفعال است")
        return existing["id"]
    return insert_row("project_roles", {"name": cleaned, "is_active": True})


def _project_role_id(fields: dict) -> int:
    """شناسه نقش را از شناسهٔ موجود یا نام تازه برمی‌گرداند."""
    if fields.get("project_role_id") is not None:
        return resolve_lookup_id("project_roles", fields.get("project_role_id"), None)
    return ensure_project_role(fields.get("project_role"))


def insert_project_member(fields: dict, actor_id=None) -> int:
    """یک کاربر را با نقش داخل پروژه به پروژه اضافه می‌کند."""
    project = fetch_project(fields["project_id"])
    user = fetch_user(fields["user_id"])
    if not user["is_active"]:
        raise InvalidInputError("کاربر غیرفعال را نمی‌توان به پروژه اضافه کرد")
    role_id = _project_role_id(fields)
    role_name_row = fetch_first(
        "project_roles",
        {"id": role_id},
        columns=("id", "name"),
    )
    role_name = role_name_row["name"] if role_name_row else ""
    values = {
        "project_id": fields["project_id"],
        "user_id": fields["user_id"],
        "project_role_id": role_id,
        "is_active": True,
    }

    def work(connection):
        row_id = insert_row_on(connection, "project_members", values)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "ProjectMember",
            row_id,
            None,
            {
                "project_id": fields["project_id"],
                "user_id": fields["user_id"],
                "project_role": role_name,
            },
        )
        insert_notification_on(
            connection,
            fields["user_id"],
            TYPE_ADDED_TO_PROJECT,
            f"به پروژه {project['name']} اضافه شدی.",
        )
        return row_id

    return run_query(work, unique_messages_for("project_members"))


def update_project_member(fields: dict, actor_id=None) -> int:
    """نقش داخل پروژه یا فعال بودن عضویت را عوض می‌کند."""
    row_id = fields.get("id")
    if not isinstance(row_id, int) or isinstance(row_id, bool) or row_id < 1:
        raise InvalidInputError("شناسه عضویت نامعتبر است")
    existing = fetch_project_member(row_id)
    prepared = {"id": row_id}
    if "is_active" in fields:
        prepared["is_active"] = fields["is_active"]
    if "project_role_id" in fields or "project_role" in fields:
        prepared["project_role_id"] = _project_role_id(fields)
    if len(prepared) == 1:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    old_value = {}
    new_value = {}
    if "is_active" in prepared and prepared["is_active"] != existing["is_active"]:
        old_value["is_active"] = existing["is_active"]
        new_value["is_active"] = prepared["is_active"]
    if "project_role_id" in prepared:
        if prepared["project_role_id"] != existing["project_role_id"]:
            old_value["project_role"] = existing["project_role_name"]
            role_row = fetch_first(
                "project_roles",
                {"id": prepared["project_role_id"]},
                columns=("id", "name"),
            )
            new_value["project_role"] = role_row["name"] if role_row else ""
    updated_id = update_row(
        "project_members",
        prepared,
        ProjectMemberNotFoundError,
        _not_found_message(row_id),
    )
    record_audit(
        actor_id,
        ACTION_UPDATE,
        "ProjectMember",
        updated_id,
        old_value or None,
        new_value or {key: prepared[key] for key in prepared if key != "id"},
    )
    return updated_id


insert_project_member = logged_step("insert")(insert_project_member)
fetch_project_member = logged_step("fetch")(fetch_project_member)
fetch_project_members = logged_step("fetch")(fetch_project_members)
update_project_member = logged_step("update")(update_project_member)
