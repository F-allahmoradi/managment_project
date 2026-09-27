"""عنوان سرور و annotations ابزارهای حساب و تراکنش ساده.

تشویق/تنبیه و دفتر کل در این گام ثبت نمی‌شوند.
"""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-finance"
SERVER_TITLE = "مالی سامانه مدیریت"
SERVER_DESCRIPTION = (
    "حساب و تراکنش مالی ساده را در PostgreSQL ثبت می‌کند. "
    "منبع حقیقت تراکنش است؛ ماندهٔ حساب از جمع تراکنش‌ها می‌آید. "
    "حسابداری دوطرفه و تشویق/تنبیه مال این سرور نیست."
)
SERVER_INSTRUCTIONS = (
    "ابزارهای مالی با مجوز Finance/Create و Finance/Read کار می‌کنند. "
    "create_financial_account حساب می‌سازد؛ مانده را دستی ننویسید. "
    "create_financial_transaction دریافت یا پرداخت را روی همان حساب "
    "ثبت می‌کند. مبلغ صفر رد می‌شود. دریافت مثبت و پرداخت منفی ذخیره "
    "می‌شود تا جمع تراکنش‌ها با مانده یکی باشد. "
    "project_id و user_id اختیاری‌اند. "
    "list_financial_transactions را می‌شود با حساب یا پروژه فیلتر کرد. "
    "تراکنش حذف نمی‌شود؛ جبران با ردیف بازگشت وجه است. "
    "نوع انتقال در این گام یک ردیف ساده است، نه سند دوطرفه. "
    "create_financial_category دستهٔ جدید مثل نوع هزینه را می‌افزاید. "
    "برای نوع تراکنش ابزار جدا نیست؛ نام seed مثل دریافت یا پرداخت کافی است. "
    "performance_actions و داشبورد هزینه در stats مال این سرور نیستند."
)

TITLE_CREATE_FINANCIAL_ACCOUNT = "ثبت حساب مالی"
TITLE_GET_FINANCIAL_ACCOUNT = "خواندن حساب مالی"
TITLE_LIST_FINANCIAL_ACCOUNTS = "فهرست حساب‌های مالی"
TITLE_CREATE_FINANCIAL_TRANSACTION = "ثبت تراکنش مالی"
TITLE_LIST_FINANCIAL_TRANSACTIONS = "فهرست تراکنش‌های مالی"
TITLE_CREATE_FINANCIAL_CATEGORY = "افزودن دسته مالی"

READ_ONLY_FINANCE = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_FINANCE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=True,
)
