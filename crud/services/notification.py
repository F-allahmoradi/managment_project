"""سرویس اعلان داخل پنل.

متن در message است؛ content_id خالی می‌ماند.
نوع از lookup seed است (وظیفه جدید، افزوده شدن به پروژه، …).
ساختن اعلان داخلی است؛ کاربر عادی create_notification ندارد.
"""

from errors.crud import (
    InvalidInputError,
    NotificationNotFoundError,
    PermissionDeniedError,
)
from logging_module import logged_step
from repository import (
    fetch_notification_record,
    fetch_notifications_for_actor_records,
    insert_row,
    insert_row_on,
    resolve_lookup_id,
    update_row,
    update_row_on,
)

TYPE_NEW_TASK = "وظیفه جدید"
TYPE_NEW_REPORT = "گزارش جدید"
TYPE_REMINDER = "یادآوری"
TYPE_TASK_STATUS = "تغییر وضعیت Task"
TYPE_ADDED_TO_PROJECT = "افزوده شدن به پروژه"


def _not_found_message(notification_id: int) -> str:
    return f"اعلان با شناسه {notification_id} پیدا نشد"


def _require_message(message) -> str:
    if message is None or not str(message).strip():
        raise InvalidInputError("متن اعلان خالی مجاز نیست")
    return message


def _notification_title(type_name: str, title=None) -> str:
    """عنوان کارت اعلان؛ اگر خالی باشد همان نام نوع seed است."""
    heading = str(title).strip() if title is not None else ""
    if not heading:
        heading = type_name
    if len(heading) > 200:
        return heading[:200]
    return heading


def insert_notification_on(
    connection,
    user_id: int,
    type_name: str,
    message: str,
    title=None,
):
    """اعلان متنی را روی اتصال باز درج می‌کند؛ content_id نمی‌نویسد."""
    type_id = resolve_lookup_id("notification_types", None, type_name)
    return insert_row_on(
        connection,
        "notifications",
        {
            "user_id": user_id,
            "notification_type_id": type_id,
            "title": _notification_title(type_name, title),
            "message": _require_message(message),
            "is_read": False,
        },
    )


def insert_notification(user_id: int, type_name: str, message: str, title=None) -> int:
    """اعلان داخلی برای یک کاربر می‌سازد؛ ابزار MCP عمومی نیست."""
    type_id = resolve_lookup_id("notification_types", None, type_name)
    return insert_row(
        "notifications",
        {
            "user_id": user_id,
            "notification_type_id": type_id,
            "title": _notification_title(type_name, title),
            "message": _require_message(message),
            "is_read": False,
        },
    )


def fetch_notification(notification_id: int) -> dict:
    """یک اعلان را با شناسه می‌خواند؛ بدون بررسی مالک."""
    row = fetch_notification_record(notification_id)
    if row is None:
        raise NotificationNotFoundError(_not_found_message(notification_id))
    return row


def fetch_own_notification(notification_id: int, user_id: int) -> dict:
    """اعلان را فقط اگر مال همین کاربر باشد برمی‌گرداند."""
    row = fetch_notification(notification_id)
    if row["user_id"] != user_id:
        raise PermissionDeniedError("فقط اعلان خودتان را می‌بینید")
    return row


def fetch_notifications_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    is_read=None,
) -> list:
    """اعلان‌های همان کاربر را می‌خواند."""
    return fetch_notifications_for_actor_records(
        user_id,
        limit,
        offset,
        is_read=is_read,
    )


def mark_notification_read_on(connection, notification_id: int, user_id: int) -> int:
    """اعلان خود کاربر را روی اتصال باز خوانده می‌کند."""
    fetch_own_notification(notification_id, user_id)
    return update_row_on(
        connection,
        "notifications",
        {"id": notification_id, "is_read": True},
        NotificationNotFoundError,
        _not_found_message(notification_id),
    )


def mark_notification_read(notification_id: int, user_id: int) -> int:
    """اعلان خود کاربر را خوانده می‌کند."""
    fetch_own_notification(notification_id, user_id)
    return update_row(
        "notifications",
        {"id": notification_id, "is_read": True},
        NotificationNotFoundError,
        _not_found_message(notification_id),
    )


insert_notification = logged_step("insert")(insert_notification)
fetch_notification = logged_step("fetch")(fetch_notification)
fetch_own_notification = logged_step("fetch")(fetch_own_notification)
fetch_notifications_for_actor = logged_step("fetch")(fetch_notifications_for_actor)
mark_notification_read = logged_step("update")(mark_notification_read)
