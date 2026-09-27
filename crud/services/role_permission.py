"""سرویس اتصال مجوز به نقش در role_permissions."""

from errors.crud import RolePermissionNotFoundError
from logging_module import logged_step
from repository import delete_row, fetch_first, fetch_role_permission_records, insert_row
from services.audit_log import ACTION_CREATE, ACTION_DELETE, record_audit
from services.permission import fetch_permission
from services.role import fetch_role


def insert_role_permission(fields: dict, actor_id=None) -> int:
    """یک مجوز را به یک نقش می‌دهد و شناسه اتصال را برمی‌گرداند."""
    fetch_role(fields["role_id"])
    fetch_permission(fields["permission_id"])
    new_id = insert_row("role_permissions", fields)
    record_audit(
        actor_id,
        ACTION_CREATE,
        "RolePermission",
        new_id,
        None,
        {
            "role_id": fields["role_id"],
            "permission_id": fields["permission_id"],
        },
    )
    return new_id


def fetch_role_permissions(role_id, limit: int, offset: int) -> list:
    """اتصال‌های نقش-مجوز را با جزئیات مجوز می‌خواند."""
    if role_id is not None:
        fetch_role(role_id)
    return fetch_role_permission_records(role_id, limit, offset)


def delete_role_permission(row_id: int, actor_id=None) -> int:
    """یک مجوز را از نقش می‌گیرد."""
    existing = fetch_first(
        "role_permissions",
        {"id": row_id},
        columns=("id", "role_id", "permission_id"),
    )
    if existing is None:
        raise RolePermissionNotFoundError(
            f"اتصال نقش-مجوز با شناسه {row_id} پیدا نشد"
        )
    deleted_id = delete_row(
        "role_permissions",
        row_id,
        RolePermissionNotFoundError,
        f"اتصال نقش-مجوز با شناسه {row_id} پیدا نشد",
    )
    record_audit(
        actor_id,
        ACTION_DELETE,
        "RolePermission",
        deleted_id,
        {
            "role_id": existing.get("role_id"),
            "permission_id": existing.get("permission_id"),
        },
        None,
    )
    return deleted_id


insert_role_permission = logged_step("insert")(insert_role_permission)
fetch_role_permissions = logged_step("fetch")(fetch_role_permissions)
delete_role_permission = logged_step("delete")(delete_role_permission)
