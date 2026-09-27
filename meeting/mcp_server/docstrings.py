"""توضیح کامل هر ابزار جلسه برای description روی سیم پروتکل.

ضبط و همگام‌سازی به پروژه در همین گام است.
"""

CREATE_MEETING_SCHEDULE = """
الگوی تکرار جلسهٔ مدیر را در meeting_schedules ثبت می‌کند.

چرا این ابزار:
    «جلساتم چهارشنبه‌ست ساعت ۱۰» یک عادت است، نه یک تاریخ.
    نمونه‌های مشخص بعداً با generate_meetings از روی همین الگو ساخته می‌شوند.

مجوز لازم:
    MeetingSchedule/Create برای کاربر جاری.

ورودی اجباری:
    نوع جلسه با meeting_type یا meeting_type_id (نام seed مثل جلسه تیم)،
    و روز هفته با day_of_week (۰=شنبه تا ۶=جمعه) یا day_name مثل چهارشنبه،
    و start_time مثل ۱۰:۰۰.

ورودی اختیاری:
    duration_minutes پیش‌فرض ۶۰، project_id، is_active،
    effective_from و effective_until.

خروجی:
    JSON با id الگوی جدید.
""".strip()

GET_MEETING_SCHEDULE = """
یک الگوی جلسه را با شناسه می‌خواند.

مجوز لازم:
    MeetingSchedule/Read برای کاربر جاری.
    فقط صاحب الگو یا عضو فعال پروژه‌اش می‌بیند.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با روز هفته، ساعت، مدت و نوع.
    اگر ردیف نباشد MEETING_SCHEDULE_NOT_FOUND است.
""".strip()

LIST_MEETING_SCHEDULES = """
الگوهای جلسهٔ کاربر جاری را فهرست می‌کند.

مجوز لازم:
    MeetingSchedule/Read برای کاربر جاری.

ورودی اختیاری:
    project_id، is_active، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

CREATE_MEETING = """
یک جلسه مشخص در meetings ثبت می‌کند.

چرا این ابزار:
    نمونه جدا از الگو است. مثال: چهارشنبه ۱۸ شهریور ۱۰:۰۰.
    وضعیت همیشه برنامه‌ریزی شده است. ضبط با record_meeting است.

مجوز لازم:
    Meeting/Create برای کاربر جاری.

ورودی اجباری:
    title، scheduled_at، و نوع با meeting_type یا meeting_type_id.

ورودی اختیاری:
    duration_minutes پیش‌فرض ۶۰، project_id، schedule_id،
    visibility (PRIVATE / RESTRICTED / PROJECT)، location.

خروجی:
    JSON با id جلسه جدید.
    اگر همان ساعت مدیر پر باشد MEETING_SLOT_CONFLICT است و
    suggested_at هفتهٔ بعد را می‌دهد.
    PROJECT بدون project_id برابر INVALID_INPUT است.
""".strip()

GET_MEETING = """
یک جلسه را با شناسه و فهرست شرکت‌کنندگان می‌خواند.

مجوز لازم:
    Meeting/Read برای کاربر جاری.
    مدیر، شرکت‌کنندهٔ کاربر، یا عضو پروژهٔ جلسهٔ PROJECT می‌بیند.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON جلسه به‌علاوه participants و sync_items.
    اگر ردیف نباشد MEETING_NOT_FOUND است.
""".strip()

LIST_MEETINGS = """
جلسات قابل‌مشاهدهٔ کاربر جاری را فهرست می‌کند.

مجوز لازم:
    Meeting/Read برای کاربر جاری.

ورودی اختیاری:
    project_id، status یا status_id، limit و offset؛ سقف ۵۰.

خروجی:
    JSON با records، limit و offset. فهرست خالی خطا نیست.
""".strip()

CANCEL_MEETING = """
جلسهٔ برنامه‌ریزی‌شده را لغو می‌کند؛ ردیف حذف نمی‌شود.

مجوز لازم:
    Meeting/Update برای کاربر جاری. فقط مدیر همان جلسه.

ورودی اجباری:
    id عدد صحیح مثبت.

خروجی:
    JSON با id جلسهٔ لغو شده.
    جلسهٔ از قبل لغو شده INVALID_INPUT است.
""".strip()

CREATE_MEETING_PARTICIPANT = """
یک شرکت‌کننده به جلسه موجود اضافه می‌کند.

قانون XOR مثل گیرندهٔ پیام: دقیقاً یکی از user_id یا
external_contact_id. هر دو با هم روی یک ردیف رد می‌شود.
کاربر سامانه و مخاطب خارجی می‌توانند هر دو روی یک جلسه بنشینند،
ولی در دو ردیف جدا.

مجوز لازم:
    Meeting/Update برای کاربر جاری. فقط مدیر همان جلسه.

ورودی اجباری:
    meeting_id، و دقیقاً یکی از user_id یا external_contact_id.

ورودی اختیاری:
    role.

خروجی:
    JSON با id شرکت‌کننده.
""".strip()

GENERATE_MEETINGS = """
از روی الگوی تکرار، یک نمونه برای هفتهٔ هدف می‌سازد.

چرا این ابزار:
    الگو می‌گوید چهارشنبه ۱۰:۰۰؛ این ابزار تاریخ مشخص را می‌چیند.
    پیش‌فرض weeks_ahead=1 یعنی هفتهٔ بعد.
    منطق «این هفته پره، هفته بعد؟» در کد است نه در دیتابیس.
    اگر همان ساعت پر باشد جلسه ساخته نمی‌شود و suggested_at
    هفتهٔ بعد را برمی‌گرداند؛ status برابر success می‌ماند.

مجوز لازم:
    Meeting/Create برای کاربر جاری. فقط صاحب الگو.

ورودی اجباری:
    schedule_id.

ورودی اختیاری:
    weeks_ahead پیش‌فرض ۱ (۰ همین هفته)، title، visibility.

خروجی:
    اگر ساخته شود: created=true و id و scheduled_at.
    اگر تداخل باشد: created=false، conflict=true، suggested_at.
""".strip()

RECORD_MEETING = """
محتوای ضبط را به جلسه وصل می‌کند و وضعیت را ضبط شده می‌کند.

چرا این ابزار:
    متن یا صوت قبلاً با create_content در crud ساخته شده.
    اینجا فقط content_id روی meetings می‌نشیند.

مجوز لازم:
    Meeting/Update برای کاربر جاری. فقط مدیر همان جلسه.

ورودی اجباری:
    id جلسه و content_id از contents.
    نوع محتوا TEXT یا VOICE.

خروجی:
    JSON با id جلسه و content_id.
    جلسهٔ لغو شده یا همگام‌شده INVALID_INPUT است.
    نبود محتوا CONTENT_NOT_FOUND است.
""".strip()

SYNC_MEETING = """
از روی ضبط جلسه، خروجی را در جداول موجود پروژه می‌سازد.

چرا این ابزار:
    وظیفه و پیام جدول جدید نمی‌گیرند.
    هر خروجی یک ردیف جدا در meeting_sync_items است.
    متن از contents.text_body یا notes می‌آید؛ NLP ژانر را جدا استخراج می‌کند.

قواعد:
    جلسه تیم با visibility برابر PROJECT در صورت مسئول، وظیفه می‌سازد.
    مذاکره خارجی/حقوقی یا RESTRICTED فقط با confirm=true.
    جلسه PRIVATE یا بدون پروژه رد می‌شود.

مجوز لازم:
    MeetingSync/Execute برای کاربر جاری. فقط مدیر همان جلسه.

ورودی اجباری:
    id جلسهٔ ضبط‌شده.

ورودی اختیاری:
    confirm، notes، decision_title (عنوان کمکی وظیفه)،
    task_title، assigned_to_user_id، task_id، chat_id، message_text
    و گیرندهٔ پیام.

خروجی:
    JSON با sync_status (SYNCED یا PARTIAL) و شناسهٔ وظیفه/پیام.
    اگر همه ساخته شود وضعیت جلسه همگام‌سازی شده می‌شود.
""".strip()
