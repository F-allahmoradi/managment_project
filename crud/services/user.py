"""سرویس عملیات جدول users.

SQL در repository است. اینجا فقط هش رمز و پیام دامنه است.
"""

from pathlib import Path
import sys

from errors.crud import InvalidInputError, UserNotFoundError
from logging_module import logged_step
from repository import (
    delete_row,
    fetch_assignable_user_records,
    fetch_row,
    fetch_rows,
    insert_row,
    update_row,
)
from services.audit_log import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, record_audit

_REPO = Path(__file__).resolve().parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from auth.hash_password import hash_password


def _not_found_message(user_id: int) -> str:
    return f"کاربر با شناسه {user_id} پیدا نشد"


def _prepare_write(fields: dict) -> dict:
    """password خام را هش می‌کند و password_hash کلاینت را دور می‌ریزد."""
    prepared = {
        key: value
        for key, value in fields.items()
        if key not in ("id", "password", "password_hash", "created_at")
    }
    password = fields.get("password")
    if password is not None:
        prepared["password_hash"] = hash_password(password)
    return prepared


def insert_user(fields: dict, actor_id=None) -> int:
    """یک ردیف جدید در users درج می‌کند و شناسه را برمی‌گرداند."""
    prepared = _prepare_write(fields)
    if "password_hash" not in prepared:
        raise InvalidInputError("رمز برای ساخت کاربر لازم است")
    new_id = insert_row("users", prepared)
    record_audit(
        actor_id,
        ACTION_CREATE,
        "User",
        new_id,
        None,
        {
            "username": prepared.get("username"),
            "first_name": prepared.get("first_name"),
            "last_name": prepared.get("last_name"),
            "is_active": prepared.get("is_active"),
        },
    )
    return new_id


def fetch_user(user_id: int) -> dict:
    """یک کاربر فعال را با شناسه می‌خواند."""
    row = fetch_row(
        "users",
        user_id,
        UserNotFoundError,
        _not_found_message(user_id),
    )
    if not row.get("is_active"):
        raise UserNotFoundError(_not_found_message(user_id))
    return row


def fetch_users(limit: int, offset: int) -> list:
    """چند ردیف users را با LIMIT و OFFSET می‌خواند."""
    return fetch_rows("users", limit, offset)


def fetch_assignable_users(limit: int, offset: int, registered_only: bool) -> list:
    """کاربران قابل‌تعیین‌دسترسی را برای بازیگر جاری می‌خواند."""
    return fetch_assignable_user_records(limit, offset, registered_only)


def update_user(fields: dict, actor_id=None) -> int:
    """یک ردیف موجود users را به‌روز می‌کند و شناسه را برمی‌گرداند."""
    user_id = fields.get("id")
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise InvalidInputError("شناسه کاربر نامعتبر است")
    prepared = _prepare_write(fields)
    if not prepared:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    existing = fetch_user(user_id)
    prepared["id"] = user_id
    updated_id = update_row(
        "users",
        prepared,
        UserNotFoundError,
        _not_found_message(user_id),
    )
    new_value = {
        key: prepared[key]
        for key in prepared
        if key not in ("id", "password_hash")
    }
    old_value = {key: existing.get(key) for key in new_value if key in existing}
    record_audit(actor_id, ACTION_UPDATE, "User", updated_id, old_value, new_value)
    return updated_id


def delete_user(user_id: int, actor_id=None) -> int:
    """کاربر را غیرفعال می‌کند (is_active=false)؛ ردیف حذف نمی‌شود."""
    existing = fetch_user(user_id)
    deleted_id = delete_row(
        "users",
        user_id,
        UserNotFoundError,
        _not_found_message(user_id),
    )
    record_audit(
        actor_id,
        ACTION_DELETE,
        "User",
        deleted_id,
        {
            "username": existing.get("username"),
            "first_name": existing.get("first_name"),
            "last_name": existing.get("last_name"),
        },
        None,
    )
    return deleted_id


insert_user = logged_step("insert")(insert_user)
fetch_user = logged_step("fetch")(fetch_user)
fetch_users = logged_step("fetch")(fetch_users)
fetch_assignable_users = logged_step("fetch")(fetch_assignable_users)
update_user = logged_step("update")(update_user)
delete_user = logged_step("delete")(delete_user)
