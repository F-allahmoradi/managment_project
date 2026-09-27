"""سرویس عملیات جدول permissions."""

from errors.crud import InvalidInputError, PermissionNotFoundError
from logging_module import logged_step
from repository import fetch_row, fetch_rows, insert_row
from services.audit_log import ACTION_CREATE, record_audit


def insert_permission(fields: dict, actor_id=None) -> int:
    """یک مجوز ریز در permissions درج می‌کند و شناسه را برمی‌گرداند."""
    if not fields.get("name") or not fields.get("resource") or not fields.get("action"):
        raise InvalidInputError("نام و resource و action برای مجوز لازم است")
    new_id = insert_row("permissions", fields)
    record_audit(
        actor_id,
        ACTION_CREATE,
        "Permission",
        new_id,
        None,
        {
            "name": fields.get("name"),
            "resource": fields.get("resource"),
            "action": fields.get("action"),
        },
    )
    return new_id


def fetch_permission(permission_id: int) -> dict:
    """یک مجوز را با شناسه می‌خواند."""
    return fetch_row(
        "permissions",
        permission_id,
        PermissionNotFoundError,
        f"مجوز با شناسه {permission_id} پیدا نشد",
    )


def fetch_permissions(limit: int, offset: int) -> list:
    """چند مجوز را با LIMIT و OFFSET می‌خواند."""
    return fetch_rows("permissions", limit, offset)


insert_permission = logged_step("insert")(insert_permission)
fetch_permission = logged_step("fetch")(fetch_permission)
fetch_permissions = logged_step("fetch")(fetch_permissions)
