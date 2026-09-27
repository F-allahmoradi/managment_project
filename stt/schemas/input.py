"""مدل اعتبارسنجی ورودی ضبط، رونویسی فایل، و ذخیره متن."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

_LANGUAGES = frozenset({"fa-IR", "en-US", "ar-SA"})
_QUALITIES = frozenset({"low", "medium", "high"})


def _reject_bool_for_int(value):
    if isinstance(value, bool):
        raise ValueError("باید عدد صحیح باشد نه بولین")
    return value


class TranscribeAudioInput(BaseModel):
    """ورودی تبدیل فایل صوتی محلی به متن."""

    file_path: str = Field(min_length=1, max_length=2000, description="مسیر فایل صوتی")
    language: str = Field(default="fa-IR", description="کد زبان موتور گفتار")
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("file_path")
    @classmethod
    def _path_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("مسیر فایل خالی است")
        return value

    @field_validator("language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        code = value.strip()
        if code not in _LANGUAGES:
            raise ValueError("زبان باید fa-IR یا en-US یا ar-SA باشد")
        return code


class RecordAudioInput(BaseModel):
    """ورودی ضبط میکروفون همین ماشین."""

    language: str = Field(default="fa-IR")
    timeout: int = Field(default=5, ge=1, le=15)
    phrase_time_limit: int = Field(default=10, ge=1, le=60)
    quality: str = Field(default="medium")
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("timeout", "phrase_time_limit", mode="before")
    @classmethod
    def _reject_bool(cls, value):
        return _reject_bool_for_int(value)

    @field_validator("language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        code = value.strip()
        if code not in _LANGUAGES:
            raise ValueError("زبان باید fa-IR یا en-US یا ar-SA باشد")
        return code

    @field_validator("quality")
    @classmethod
    def _known_quality(cls, value: str) -> str:
        code = value.strip().lower()
        if code not in _QUALITIES:
            raise ValueError("quality باید low یا medium یا high باشد")
        return code


class SaveTranscriptInput(BaseModel):
    """ورودی ذخیره متن و در صورت وجود فایل، خود صوت."""

    text: str = Field(min_length=1, description="متن استخراج‌شده")
    file_path: str | None = Field(default=None, description="مسیر فایل صوتی محلی")
    mime_type: str | None = Field(default=None, max_length=120)
    original_filename: str | None = Field(default=None, max_length=255)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("text")
    @classmethod
    def _text_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("متن خالی است")
        return value

    @field_validator("file_path", "mime_type", "original_filename")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None or not value:
            return None
        return value


class DeleteTranscriptInput(BaseModel):
    """ورودی حذف نرم متن ذخیره‌شده."""

    id: int = Field(ge=1, description="شناسه contents")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool(cls, value):
        return _reject_bool_for_int(value)
