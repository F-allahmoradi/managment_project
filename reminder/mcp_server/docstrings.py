"""توضیح کامل هر ابزار تعریف و ارسال یادآوری برای description روی سیم پروتکل."""

CREATE_REMINDER = """
یک یادآوری جدید در جدول reminders ثبت می‌کند و گیرنده‌ها را همان لحظه می‌سازد.

چرا این ابزار:
    تعریف «چه چیزی باید یادآوری شود» از ارسال واقعی جدا است.
    متن در message_template است. content_id و task_item_id نوشته نمی‌شوند.
    برای هر گیرنده یک follow_up_states با «در انتظار» ساخته می‌شود
    بدون اینکه پیامی برود.

قانون گیرنده:
    حداقل یک گیرنده لازم است.
    target_user_id و target_external_contact_id اگر هر دو بیایند
    دو ردیف جدا می‌سازند. هر ردیف دقیقاً یکی از user یا external است.

قانون پروژه:
    project_id اختیاری است. اگر بیاید سازنده باید عضو فعال همان پروژه باشد.

مجوز لازم:
    Reminder/Create برای کاربر جاری.
    اگر project_id بیاید، عضویت فعال همان پروژه هم لازم است.

ورودی اجباری:
    title، message_template، scheduled_at،
    نوع (reminder_type یا reminder_type_id)،
    تکرار (frequency یا frequency_id)،
    و حداقل یکی از target_user_id یا target_external_contact_id.
    نام lookup از seed است؛ مثل یک‌باره، هفتگی، پیگیری.

ورودی اختیاری:
    project_id، next_run_at (پیش‌فرض همان scheduled_at)،
    status یا status_id (پیش‌فرض فعال).

خروجی:
    JSON با id یادآوری جدید.
    بدون گیرنده یا متن خالی INVALID_INPUT است.
    گیرندهٔ دوگانه روی یک ردیف INVALID_INPUT است.
""".strip()

GET_REMINDER = """
یک یادآوری را با شناسه می‌خواند؛ فقط اگر سازنده، گیرندهٔ کاربر،
یا عضو فعال پروژهٔ همان یادآوری باشید.

مجوز لازم:
    Reminder/Read و دسترسی به همان یادآوری.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با عنوان، متن، زمان، تکرار و وضعیت.
    content_id و task_item_id در پاسخ نیستند.
    اگر ردیف نباشد REMINDER_NOT_FOUND است.
""".strip()

LIST_REMINDERS = """
یادآوری‌هایی را فهرست می‌کند که سازنده‌شان هستید، گیرنده‌شان هستید،
یا روی پروژهٔ عضو فعال بودنتان‌اند.

مجوز لازم:
    Reminder/Read برای کاربر جاری.
    اگر project_id بیاید، عضویت فعال همان پروژه هم لازم است.

ورودی اختیاری:
    project_id، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

UPDATE_REMINDER = """
تعریف یک یادآوری موجود را به‌روز می‌کند.

وضعیت را می‌توان به متوقف یا لغو شده عوض کرد. ارسال رخ نمی‌دهد.
گیرنده‌ها و follow_up_states در این ابزار عوض نمی‌شوند.

مجوز لازم:
    Reminder/Create.
    اگر یادآوری به پروژه وصل باشد، عضویت فعال همان پروژه لازم است.
    اگر project_id خالی باشد فقط سازنده می‌تواند عوض کند.

ورودی اجباری:
    id.

ورودی اختیاری:
    title، message_template، scheduled_at، next_run_at،
    نوع، تکرار، وضعیت. حداقل یکی لازم است.
""".strip()

LIST_FOLLOW_UP_STATES = """
وضعیت پیگیری هر گیرندهٔ یک یادآوری را می‌خواند.

قبل از ارسال، گیرنده‌ها «در انتظار» با attempt_count برابر ۰ هستند.
بعد از send_reminder، last_sent_at پر می‌شود و attempt_count زیاد می‌شود.
وضعیت تا پاسخ گیرنده «در انتظار» می‌ماند.

مجوز لازم:
    Reminder/Read و دسترسی به همان یادآوری.

ورودی اجباری:
    reminder_id.

ورودی اختیاری:
    limit و offset.
""".strip()

SEND_REMINDER = """
یادآوری فعال را روی کانال INTERNAL می‌فرستد.

برای کاربر سامانه یک اعلان پنل با نوع «یادآوری» ساخته می‌شود؛
عنوان کارت همان عنوان یادآوری است.
برای مخاطب خارجی فقط ردیف execution_logs ثبت می‌شود.
تلگرام در این گام نیست.

هر گیرنده یک ردیف execution_logs با idempotency_key می‌گیرد.
تکرار همان کلید اعلان و لاگ جدید نمی‌سازد.

اگر گیرنده مشخص نشود برای همهٔ گیرنده‌ها می‌فرستد.
کلید دستی فقط با دقیقاً یک گیرنده مجاز است.

مجوز لازم:
    Reminder/Dispatch.
    اگر یادآوری به پروژه وصل باشد، عضویت فعال همان پروژه لازم است.
    اگر project_id خالی باشد فقط سازنده می‌تواند بفرستد.

ورودی اجباری:
    reminder_id.

ورودی اختیاری:
    target_user_id یا target_external_contact_id،
    channel (پیش‌فرض INTERNAL)، idempotency_key.

خروجی:
    JSON با records لاگ، sent_count و replayed_count.
    یادآوری غیر فعال INVALID_INPUT است.
""".strip()

RETRY_REMINDER = """
تلاش بعدی ارسال همان یادآوری را با کلید idempotency جدا می‌نویسد.

باید قبلاً send_reminder شده باشد. شماره تلاش یکی زیاد می‌شود.
تکرار همان کلید تلاش مجدد پیام دوبل نمی‌سازد.

مجوز لازم:
    Reminder/Dispatch؛ همان قانون نوشتن send_reminder.

ورودی اجباری:
    reminder_id.

ورودی اختیاری:
    همان فیلدهای send_reminder.
""".strip()

LIST_EXECUTION_LOGS = """
تاریخچهٔ ارسال واقعی یک یادآوری را از execution_logs می‌خواند.

مجوز لازم:
    Reminder/Read و دسترسی به همان یادآوری.

ورودی اجباری:
    reminder_id.

ورودی اختیاری:
    limit و offset.
""".strip()
