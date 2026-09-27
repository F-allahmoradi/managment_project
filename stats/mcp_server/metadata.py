"""عنوان سرور و annotations ابزارهای آمار فقط‌خواندنی.

گزارش متنی و پیش‌بینی احتمال تأخیر مال این سرور نیست.
"""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-stats"
SERVER_TITLE = "آمار سامانه مدیریت"
SERVER_DESCRIPTION = (
    "داشبورد و آمار فقط‌خواندنی پروژه، وظیفه، عضو، پیگیری، پیام، "
    "عملکرد، مالی و ارسال یادآوری را از PostgreSQL برمی‌گرداند. "
    "هیچ INSERT یا UPDATE یا DELETE ندارد. گزارش متنی سرور جدا است."
)
SERVER_INSTRUCTIONS = (
    "همهٔ ابزارها read-only هستند و فقط پروژه‌هایی را می‌بینند که "
    "کاربر جاری عضو فعال‌شان است. "
    "get_project_progress درصد وظایف با وضعیت تکمیل شده است. "
    "get_project_health همان عدد را با برچسب سالم یا در معرض تأخیر "
    "یا تأخیر می‌دهد. list_at_risk_projects پروژه‌های عقب‌افتاده را "
    "فهرست می‌کند. "
    "get_overdue_tasks ردیف وظایف گذشته از مهلت را برمی‌گرداند. "
    "get_task_status_breakdown توزیع وضعیت‌هاست و "
    "get_task_completion_stats نرخ تکمیل. "
    "get_member_workload بار کاری هر عضو است؛ "
    "list_members_needing_attention کسانی است که وظیفهٔ عقب‌افتاده دارند. "
    "get_follow_up_counts شمار پیگیری هر وظیفه است و "
    "get_repeated_follow_ups آن‌هایی که از آستانه بیشتر پیگیری شده‌اند. "
    "get_message_type_counts شمار هشدار و درخواست اقدام است. "
    "get_member_scores و get_performance_dashboard امتیاز و تشویق/تنبیه. "
    "get_project_costs و get_transaction_summary جمع تراکنش. "
    "get_delivery_stats ارسال موفق و ناموفق بعد از dispatch. "
    "کاربر بدون عضویت فعال آمار آن پروژه را نمی‌بیند. "
    "متن طولانی گزارش مال سرور report است نه اینجا."
)

TITLE_GET_PROJECT_PROGRESS = "پیشرفت پروژه"
TITLE_GET_PROJECT_HEALTH = "سلامت پروژه"
TITLE_LIST_AT_RISK_PROJECTS = "پروژه‌های در معرض تأخیر"
TITLE_GET_OVERDUE_TASKS = "وظایف عقب‌افتاده"
TITLE_GET_TASK_STATUS_BREAKDOWN = "توزیع وضعیت وظایف"
TITLE_GET_TASK_COMPLETION_STATS = "نرخ تکمیل وظایف"
TITLE_GET_MEMBER_WORKLOAD = "بار کاری اعضا"
TITLE_LIST_MEMBERS_NEEDING_ATTENTION = "اعضای نیازمند پیگیری"
TITLE_GET_FOLLOW_UP_COUNTS = "شمار پیگیری وظایف"
TITLE_GET_REPEATED_FOLLOW_UPS = "پیگیری‌های تکراری"
TITLE_GET_MESSAGE_TYPE_COUNTS = "شمار نوع پیام"
TITLE_GET_MEMBER_SCORES = "امتیاز اعضا"
TITLE_GET_PERFORMANCE_DASHBOARD = "داشبورد عملکرد"
TITLE_GET_PROJECT_COSTS = "هزینه پروژه"
TITLE_GET_TRANSACTION_SUMMARY = "خلاصه تراکنش‌ها"
TITLE_GET_DELIVERY_STATS = "آمار ارسال یادآوری"

READ_ONLY_STATS = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
