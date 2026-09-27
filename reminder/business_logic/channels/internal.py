"""ارسال کانال INTERNAL: اعلان پنل برای کاربر، رکورد داخلی برای مخاطب خارجی."""

from services.notification import TYPE_REMINDER, insert_notification_on


def deliver_internal(connection, reminder: dict, target: dict) -> dict:
    """متن یادآوری را داخل سامانه می‌رساند؛ تلگرام نیست.

    برای کاربر سامانه یک ردیف notifications با نوع «یادآوری» ساخته می‌شود؛
    عنوان کارت همان عنوان یادآوری است.
    مخاطب خارجی جدول اعلان ندارد؛ فقط متن رندرشده برمی‌گردد تا در
    execution_logs بماند.
    """
    rendered = reminder["message_template"]
    notification_id = None
    user_id = target.get("user_id")
    if user_id is not None:
        notification_id = insert_notification_on(
            connection,
            user_id,
            TYPE_REMINDER,
            rendered,
            title=reminder.get("title"),
        )
    return {
        "rendered_message": rendered,
        "notification_id": notification_id,
    }
