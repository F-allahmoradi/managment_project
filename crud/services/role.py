"""سرویس عملیات جدول roles.

نقش‌های seed با is_system_role حذف یا تغییرنام نمی‌شوند.
"""

from errors.crud import InvalidInputError, RoleNotFoundError
from logging_module import logged_step
from repository import delete_row, fetch_first, fetch_row, fetch_rows, insert_row, update_row
from services.audit_log import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, record_audit


def _not_found_message(role_id: int) -> str:
    return f"نقش با شناسه {role_id} پیدا نشد"


def insert_role(fields: dict, actor_id=None) -> int:
    """یک نقش غیرسیستمی در roles درج می‌کند و شناسه را برمی‌گرداند."""
    if not fields.get("name"):
        raise InvalidInputError("نام نقش لازم است")
    new_id = insert_row("roles", fields)
    record_audit(
        actor_id,
        ACTION_CREATE,
        "Role",
        new_id,
        None,
        {"name": fields.get("name"), "is_active": fields.get("is_active")},
    )
    return new_id


def fetch_role(role_id: int) -> dict:
    """یک نقش فعال را با شناسه می‌خواند."""
    row = fetch_row(
        "roles",
        role_id,
        RoleNotFoundError,
        _not_found_message(role_id),
    )
    if not row.get("is_active"):
        raise RoleNotFoundError(_not_found_message(role_id))
    return row


def fetch_roles(limit: int, offset: int) -> list:
    """چند نقش را با LIMIT و OFFSET می‌خواند."""
    return fetch_rows("roles", limit, offset)


def update_role(fields: dict, actor_id=None) -> int:
    """یک نقش موجود را به‌روز می‌کند؛ نام نقش سیستمی عوض نمی‌شود."""
    role_id = fields.get("id")
    if not isinstance(role_id, int) or isinstance(role_id, bool) or role_id < 1:
        raise InvalidInputError("شناسه نقش نامعتبر است")
    existing = fetch_role(role_id)
    if existing["is_system_role"] and "name" in fields:
        if fields["name"] != existing["name"]:
            raise InvalidInputError("نام نقش سیستمی قابل تغییر نیست")
    updated_id = update_row(
        "roles",
        fields,
        RoleNotFoundError,
        _not_found_message(role_id),
    )
    new_value = {key: fields[key] for key in fields if key != "id"}
    old_value = {key: existing.get(key) for key in new_value if key in existing}
    record_audit(actor_id, ACTION_UPDATE, "Role", updated_id, old_value, new_value)
    return updated_id


def delete_role(role_id: int, actor_id=None) -> int:
    """نقش غیرسیستمی را غیرفعال می‌کند؛ اتصال‌های user_roles در DB می‌مانند."""
    existing = fetch_role(role_id)
    if existing["is_system_role"]:
        raise InvalidInputError("نقش سیستمی قابل حذف نیست")
    deleted_id = delete_row(
        "roles",
        role_id,
        RoleNotFoundError,
        _not_found_message(role_id),
    )
    record_audit(
        actor_id,
        ACTION_DELETE,
        "Role",
        deleted_id,
        {"name": existing.get("name")},
        None,
    )
    return deleted_id


insert_role = logged_step("insert")(insert_role)
fetch_role = logged_step("fetch")(fetch_role)
fetch_roles = logged_step("fetch")(fetch_roles)
update_role = logged_step("update")(update_role)
delete_role = logged_step("delete")(delete_role)
