"""اعتبارسنجی ورودی ابزارهای اعلان داخل پنل."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_get_notification(notification_id: int) -> int:
    """شناسه خواندن اعلان را با اسکیما بررسی می‌کند."""
    from schemas.crud.notification import GetNotificationInput

    return parse_id(GetNotificationInput, notification_id)


def validate_list_notifications(is_read=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر خوانده‌شدن فهرست اعلان را بررسی می‌کند."""
    from schemas.crud.notification import ListNotificationsInput

    return parse_optional(ListNotificationsInput, is_read=is_read, limit=limit, offset=offset)


def validate_mark_notification_read(notification_id: int) -> int:
    """شناسه علامت‌زدن اعلان را با اسکیما بررسی می‌کند."""
    from schemas.crud.notification import MarkNotificationReadInput

    return parse_id(MarkNotificationReadInput, notification_id)


validate_get_notification = logged_step("validate")(validate_get_notification)
validate_list_notifications = logged_step("validate")(validate_list_notifications)
validate_mark_notification_read = logged_step("validate")(
    validate_mark_notification_read
)
