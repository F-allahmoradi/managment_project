"""توضیح کامل ابزارهای تبدیل گفتار برای description روی سیم پروتکل."""

TRANSCRIBE_AUDIO = """
فایل صوتی محلی را به متن فارسی تبدیل می‌کند.

چرا این ابزار:
    contents صوت را فقط با متادیتا نگه می‌دارد. رونویسی اینجا جداست.
    موتور Google Web Speech با زبان fa-IR همان مدل پروژه ایجنت وقایع است.
    قبل از ارسال، ffmpeg فایل را مونو ۱۶ کیلوهرتز می‌کند.

مجوز لازم:
    Content/Read.

ورودی اجباری:
    file_path مسیر مطلق یا نسبی فایل روی همین ماشین.

ورودی اختیاری:
    language مثل fa-IR یا en-US.

خروجی:
    JSON با transcribed_text و language.
    اگر فایل نباشد INVALID_INPUT است.
    اگر صدا فهمیده نشود STT_UNRECOGNIZED است.
""".strip()

RECORD_AUDIO_TO_TEXT = """
میکروفون همین ماشین را باز می‌کند و تا سکوت ضبط می‌کند، بعد متن می‌سازد.

مجوز لازم:
    Content/Create.

ورودی اختیاری:
    language پیش‌فرض fa-IR.
    timeout ثانیه انتظار برای شروع صحبت، ۱ تا ۱۵.
    phrase_time_limit حداکثر طول جمله، ۱ تا ۶۰.
    quality low یا medium یا high برای حساسیت نویز.

خروجی:
    JSON با transcribed_text.
    اگر کسی صحبت نکند STT_TIMEOUT است.
    این ابزار میکروفون مرورگر کاربر Cursor را باز نمی‌کند.
""".strip()

SAVE_TRANSCRIPT = """
متن استخراج‌شده را ذخیره می‌کند. اگر file_path بیاید، خود فایل صوت
هم روی دیسک می‌رود و یک ردیف VOICE با caption متن ساخته می‌شود.

مجوز لازم:
    Content/Create.

ورودی اجباری:
    text متن رونویسی.

ورودی اختیاری:
    file_path مسیر فایل صوتی محلی.
    mime_type و original_filename.

خروجی:
    JSON با id ردیف contents و content_kind برابر TEXT یا VOICE.
""".strip()

DELETE_TRANSCRIPT = """
متن ذخیره‌شدهٔ رونویسی را از contents نرم‌حذف می‌کند.

مجوز لازم:
    Content/Delete.

ورودی اجباری:
    id شناسه ردیف contents که save_transcript برگرداند.

خروجی:
    JSON با id. ردیف دیده نمی‌شود ولی در پایگاه می‌ماند.
    اگر نباشد CONTENT_NOT_FOUND است.
""".strip()
