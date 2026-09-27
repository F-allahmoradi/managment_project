"""توضیح کامل هر ابزار آمار برای description روی سیم پروتکل.

همه فقط‌خواندنی‌اند. گزارش متنی اینجا نیست.
"""

GET_PROJECT_PROGRESS = """
درصد پیشرفت یک پروژه را از شمار وظایف و وضعیت «تکمیل شده» حساب می‌کند.

چرا این ابزار:
    مدیر می‌پرسد چند درصد کار تمام شده؛ بدون چند بار list_tasks.

مجوز لازم:
    Project/Read و عضویت فعال همان پروژه.

ورودی اجباری:
    project_id عدد صحیح مثبت.

خروجی:
    JSON با task_count، completed_count، cancelled_count، open_count،
    overdue_count و progress_percent.
    اگر عضو نباشد PERMISSION_DENIED است.
""".strip()

GET_PROJECT_HEALTH = """
وضعیت کلی پروژه را با درصد پیشرفت و برچسب سلامت برمی‌گرداند.

برچسب‌ها از عدد است نه از مدل زبانی: سالم، در معرض تأخیر، تأخیر.

مجوز لازم:
    Project/Read و عضویت فعال همان پروژه.

ورودی اجباری:
    project_id.

خروجی:
    همان فیلدهای پیشرفت به‌علاوه health و days_remaining.
""".strip()

LIST_AT_RISK_PROJECTS = """
پروژه‌هایی را فهرست می‌کند که وظیفهٔ عقب‌افتاده دارند یا از مهلت پروژه گذشته‌اند.

فقط پروژه‌هایی که کاربر عضو فعال‌شان است.

مجوز لازم:
    Project/Read.

ورودی اختیاری:
    limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records. فهرست خالی خطا نیست.
""".strip()

GET_OVERDUE_TASKS = """
وظایفی را برمی‌گرداند که مهلت‌شان گذشته و هنوز تکمیل یا لغو نشده‌اند.

مجوز لازم:
    Task/Read. اگر project_id بیاید عضویت فعال همان پروژه لازم است.

ورودی اختیاری:
    project_id، limit و offset.

خروجی:
    JSON با records شامل عنوان، مهلت، مسئول و days_overdue.
""".strip()

GET_TASK_STATUS_BREAKDOWN = """
توزیع وضعیت وظایف را با GROUP BY روی task_statuses برمی‌گرداند.

مجوز لازم:
    Task/Read و در صورت فیلتر، عضویت فعال پروژه.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با records شامل status و count.
""".strip()

GET_TASK_COMPLETION_STATS = """
نرخ تکمیل وظایف را از نسبت وضعیت تکمیل شده به کل حساب می‌کند.

مجوز لازم:
    Task/Read و در صورت فیلتر، عضویت فعال پروژه.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با task_count، completed_count و completion_rate.
""".strip()

GET_MEMBER_WORKLOAD = """
بار کاری هر عضو را از وظایف تخصیص‌یافته حساب می‌کند.

مجوز لازم:
    Task/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id و user_id.

خروجی:
    JSON با records شامل open_tasks، overdue_tasks و completed_tasks.
""".strip()

LIST_MEMBERS_NEEDING_ATTENTION = """
اعضایی را برمی‌گرداند که حداقل یک وظیفهٔ عقب‌افتاده دارند.

مجوز لازم:
    Task/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با records. فهرست خالی خطا نیست.
""".strip()

GET_FOLLOW_UP_COUNTS = """
شمار ردیف‌های پیگیری هر وظیفه را برمی‌گرداند.

مجوز لازم:
    TaskFollowUp/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id، min_count، limit و offset.

خروجی:
    JSON با records شامل task_id و follow_up_count.
""".strip()

GET_REPEATED_FOLLOW_UPS = """
وظایفی را برمی‌گرداند که چند بار پیگیری شده‌اند؛ آستانه پیش‌فرض ۳ است.

مجوز لازم:
    TaskFollowUp/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id، min_count، limit و offset.

خروجی:
    JSON با records مرتب از بیشترین پیگیری.
""".strip()

GET_MESSAGE_TYPE_COUNTS = """
شمار پیام‌ها را بر اساس نوع مثل هشدار و درخواست اقدام برمی‌گرداند.

فقط گفتگوهای وصل به پروژهٔ عضو فعال.

مجوز لازم:
    Message/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با records شامل message_type و count.
""".strip()

GET_MEMBER_SCORES = """
جمع امتیاز و شمار تشویق/تنبیه هر عضو را در پروژه‌های مجاز برمی‌گرداند.

مجوز لازم:
    Performance/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id و user_id.

خروجی:
    JSON با records شامل total_score، reward_count و penalty_count.
""".strip()

GET_PERFORMANCE_DASHBOARD = """
خلاصهٔ تشویق و تنبیه محدوده را بدون متن طولانی برمی‌گرداند.

مجوز لازم:
    Performance/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با reward_count، penalty_count، total_score و total_amount.
""".strip()

GET_PROJECT_COSTS = """
جمع دریافت و پرداخت یک پروژه را از financial_transactions حساب می‌کند.

مجوز لازم:
    Finance/Read و عضویت فعال همان پروژه.

ورودی اجباری:
    project_id.

خروجی:
    JSON با income، expense و net. بدون تراکنش صفر است نه خطا.
""".strip()

GET_TRANSACTION_SUMMARY = """
جمع تراکنش‌های قابل‌مشاهده را با فیلتر اختیاری پروژه یا حساب برمی‌گرداند.

بدون project_id فقط تراکنش پروژه‌های عضو فعال یا بدون پروژه می‌آید.

مجوز لازم:
    Finance/Read. اگر project_id بیاید عضویت فعال لازم است.

ورودی اختیاری:
    project_id و account_id.

خروجی:
    JSON با income، expense، net و transaction_count.
""".strip()

GET_DELIVERY_STATS = """
شمار ارسال موفق و ناموفق یادآوری را از execution_logs برمی‌گرداند.

بعد از dispatch معنی دارد؛ بدون ارسال، فهرست خالی است.

مجوز لازم:
    Reminder/Read و در صورت فیلتر پروژه، عضویت فعال.

ورودی اختیاری:
    project_id.

خروجی:
    JSON با records شامل status و count مثل SENT و FAILED.
""".strip()
