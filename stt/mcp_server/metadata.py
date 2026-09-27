"""عنوان سرور و annotations ابزارهای ضبط و تبدیل گفتار."""

from mcp.types import ToolAnnotations

SERVER_NAME = "management-stt"
SERVER_TITLE = "ضبط و تبدیل گفتار به متن"
SERVER_DESCRIPTION = (
    "فرایند ضبط تا متن سه مرحله است: "
    "۱ ضبط فایل صوتی، ۲ تبدیل همان فایل به متن فارسی، ۳ بازبینی و ذخیره. "
    "موتور تبدیل Google Web Speech با زبان fa-IR است."
)
SERVER_INSTRUCTIONS = (
    "فرایند ثابت است و مرحله‌ها قاطی نمی‌شوند. "
    "مرحله ۱ ضبط: مرورگر یا زمین‌بازی فایل صوتی می‌سازد؛ "
    "record_audio_to_text فقط میکروفون خود سرور است و مرورگر را باز نمی‌کند. "
    "مرحله ۲ تبدیل: transcribe_audio همان فایل را می‌گیرد و transcribed_text برمی‌گرداند. "
    "webm و wav و ogg و mp3 با ffmpeg به wav می‌روند. زبان پیش‌فرض fa-IR است. "
    "مرحله ۳ ذخیره: save_transcript متن را می‌نویسد؛ اگر file_path باشد "
    "خود صوت هم می‌ماند و ردیف VOICE ساخته می‌شود. "
    "delete_transcript همان ردیف را نرم‌حذف می‌کند. "
    "تحلیل NER و NLP روی متن ذخیره‌شده جداست و جزو این سه مرحله نیست."
)

READ_ONLY_STT = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
WRITE_STT = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=True,
)
DESTRUCTIVE_STT = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    open_world_hint=True,
)

TITLE_TRANSCRIBE_AUDIO = "تبدیل فایل صوتی به متن"
TITLE_RECORD_AUDIO_TO_TEXT = "ضبط میکروفون و تبدیل به متن"
TITLE_SAVE_TRANSCRIPT = "ذخیره متن و صوت"
TITLE_DELETE_TRANSCRIPT = "حذف متن استخراج‌شده"
