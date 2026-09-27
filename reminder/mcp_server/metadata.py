"""عنوان سرور و annotations ابزارهای تعریف و ارسال یادآوری."""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-reminder"
SERVER_TITLE = "یادآوری سامانه مدیریت"
SERVER_DESCRIPTION = (
    "تعریف یادآوری را در PostgreSQL ثبت می‌کند و ارسال کانال INTERNAL "
    "را با execution_logs و follow_up_states انجام می‌دهد."
)
SERVER_INSTRUCTIONS = (
    "create_reminder با Reminder/Create متن را در message_template می‌گذارد "
    "و گیرنده‌ها را همان لحظه در reminder_targets می‌سازد. "
    "برای هر گیرنده یک follow_up_states با وضعیت «در انتظار» و "
    "attempt_count برابر ۰ ساخته می‌شود. "
    "هر گیرنده دقیقاً یکی از user یا external_contact است. "
    "project_id اختیاری است؛ اگر بیاید عضویت فعال همان پروژه لازم است. "
    "content_id و task_item_id در این گام خالی می‌مانند. "
    "next_run_at فقط ذخیره می‌شود؛ cron در این سرور نیست. "
    "list_reminders و get_reminder با Reminder/Read فقط یادآوری‌هایی را "
    "نشان می‌دهند که سازنده‌شان هستید، گیرنده‌شان هستید، یا عضو فعال "
    "پروژه‌شان هستید. "
    "update_reminder تعریف را عوض می‌کند نه ارسال را. "
    "send_reminder با Reminder/Dispatch روی کانال INTERNAL می‌فرستد: "
    "برای کاربر سامانه اعلان پنل، برای مخاطب خارجی فقط رکورد داخلی. "
    "هر ارسال یک ردیف execution_logs با idempotency_key می‌سازد. "
    "تکرار همان کلید پیام دوبل نمی‌سازد. "
    "retry_reminder تلاش بعدی است با کلید جدا. "
    "list_follow_up_states وضعیت هر گیرنده را نشان می‌دهد. "
    "list_execution_logs لاگ ارسال را می‌خواند. "
    "برای نوع و تکرار و وضعیت ابزار جدا نیست؛ نام seed مثل یک‌باره "
    "یا هفتگی یا فعال کافی است. "
    "تلگرام در این گام نیست."
)

TITLE_CREATE_REMINDER = "ثبت یادآوری"
TITLE_GET_REMINDER = "خواندن یادآوری"
TITLE_LIST_REMINDERS = "فهرست یادآوری‌ها"
TITLE_UPDATE_REMINDER = "به‌روزرسانی یادآوری"
TITLE_LIST_FOLLOW_UP_STATES = "فهرست وضعیت پیگیری گیرنده‌ها"
TITLE_SEND_REMINDER = "ارسال یادآوری"
TITLE_RETRY_REMINDER = "تلاش مجدد ارسال یادآوری"
TITLE_LIST_EXECUTION_LOGS = "فهرست لاگ ارسال یادآوری"

READ_ONLY_REMINDER = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_REMINDER = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=True,
)
