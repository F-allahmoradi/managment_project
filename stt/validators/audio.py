"""اعتبارسنجی ورودی ابزارهای تبدیل گفتار."""

from logging_module import logged_step
from schemas.input import (
    DeleteTranscriptInput,
    RecordAudioInput,
    SaveTranscriptInput,
    TranscribeAudioInput,
)


def validate_transcribe_audio(file_path: str, language: str = "fa-IR") -> dict:
    """مسیر فایل و زبان را بررسی می‌کند."""
    return TranscribeAudioInput(file_path=file_path, language=language).model_dump()


def validate_record_audio(
    language: str = "fa-IR",
    timeout: int = 5,
    phrase_time_limit: int = 10,
    quality: str = "medium",
) -> dict:
    """تنظیم میکروفون را بررسی می‌کند."""
    return RecordAudioInput(
        language=language,
        timeout=timeout,
        phrase_time_limit=phrase_time_limit,
        quality=quality,
    ).model_dump()


def validate_save_transcript(
    text: str,
    file_path: str | None = None,
    mime_type: str | None = None,
    original_filename: str | None = None,
) -> dict:
    """متن و در صورت وجود مسیر فایل صوت را بررسی می‌کند."""
    return SaveTranscriptInput(
        text=text,
        file_path=file_path,
        mime_type=mime_type,
        original_filename=original_filename,
    ).model_dump()


def validate_delete_transcript(row_id: int) -> int:
    """شناسه حذف متن را بررسی می‌کند."""
    return DeleteTranscriptInput(id=row_id).id


validate_transcribe_audio = logged_step("validate")(validate_transcribe_audio)
validate_record_audio = logged_step("validate")(validate_record_audio)
validate_save_transcript = logged_step("validate")(validate_save_transcript)
validate_delete_transcript = logged_step("validate")(validate_delete_transcript)
