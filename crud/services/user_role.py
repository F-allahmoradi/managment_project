"""سرویس اتصال نقش به کاربر در user_roles."""

from errors.crud import InvalidInputError, UserRoleNotFoundError
from logging_module import logged_step
from repository import delete_row, fetch_first, fetch_user_role_records, insert_row, update_row
from services.audit_log import ACTION_CREATE, ACTION_DELETE, record_audit
from services.role import fetch_role
from services.user import fetch_user


def insert_user_role(fields: dict, actor_id=None) -> int:
    """یک نقش را به یک کاربر می‌دهد و شناسه اتصال را برمی‌گرداند."""
    fetch_user(fields["user_id"])
    fetch_role(fields["role_id"])
    existing = fetch_first(
        "user_roles",
        {"user_id": fields["user_id"], "role_id": fields["role_id"]},
        columns=("id", "is_active"),
    )
    if existing is not None:
        if existing.get("is_active"):
            raise InvalidInputError("این نقش از قبل به کاربر داده شده")
        new_id = update_row(
            "user_roles",
            {"id": existing["id"], "is_active": True},
            UserRoleNotFoundError,
            f"اتصال کاربر-نقش با شناسه {existing['id']} پیدا نشد",
        )
        record_audit(
            actor_id,
            ACTION_CREATE,
            "UserRole",
            new_id,
            {"is_active": False},
            {"user_id": fields["user_id"], "role_id": fields["role_id"], "is_active": True},
        )
        return new_id
    new_id = insert_row("user_roles", fields)
    record_audit(
        actor_id,
        ACTION_CREATE,
        "UserRole",
        new_id,
        None,
        {"user_id": fields["user_id"], "role_id": fields["role_id"]},
    )
    return new_id


def fetch_user_roles(user_id, limit: int, offset: int) -> list:
    """اتصال‌های کاربر-نقش را با نام نقش می‌خواند."""
    if user_id is not None:
        fetch_user(user_id)
    return fetch_user_role_records(user_id, limit, offset)


def delete_user_role(row_id: int, actor_id=None) -> int:
    """یک نقش را از کاربر می‌گیرد."""
    existing = fetch_first(
        "user_roles",
        {"id": row_id},
        columns=("id", "user_id", "role_id"),
    )
    if existing is None:
        raise UserRoleNotFoundError(f"اتصال کاربر-نقش با شناسه {row_id} پیدا نشد")
    deleted_id = delete_row(
        "user_roles",
        row_id,
        UserRoleNotFoundError,
        f"اتصال کاربر-نقش با شناسه {row_id} پیدا نشد",
    )
    record_audit(
        actor_id,
        ACTION_DELETE,
        "UserRole",
        deleted_id,
        {"user_id": existing.get("user_id"), "role_id": existing.get("role_id")},
        None,
    )
    return deleted_id


insert_user_role = logged_step("insert")(insert_user_role)
fetch_user_roles = logged_step("fetch")(fetch_user_roles)
delete_user_role = logged_step("delete")(delete_user_role)
