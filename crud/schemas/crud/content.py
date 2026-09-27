"""اسکیمای ورودی ابزارهای Content.

متن خالص یا متادیتای فایل. آپلود واقعی S3 اینجا نیست؛
storage_key کافی است.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int

_KIND_ALIASES = {
    "TEXT": "TEXT",
    "VOICE": "VOICE",
    "IMAGE": "IMAGE",
    "FILE": "FILE",
    "متن": "TEXT",
    "صوت": "VOICE",
    "تصویر": "IMAGE",
    "عکس": "IMAGE",
    "فایل": "FILE",
}
_MEDIA_KINDS = frozenset({"VOICE", "IMAGE", "FILE"})
_MEDIA_LABELS = {"VOICE": "صوت", "IMAGE": "تصویر", "FILE": "فایل"}
_MEDIA_FIELDS = (
    "storage_key",
    "original_filename",
    "mime_type",
    "file_size_bytes",
    "duration_seconds",
)


class CreateContentInput(BaseModel):
    """ورودی ثبت یک واحد محتوا در contents."""

    content_kind_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در content_kinds",
    )
    content_kind: Optional[str] = Field(
        default=None,
        max_length=20,
        description="کد یا نام نوع: TEXT/متن، VOICE/صوت، IMAGE/تصویر یا FILE/فایل",
    )
    text_body: Optional[str] = Field(
        default=None,
        description="متن؛ برای TEXT الزامی است و برای فایل اختیاری به‌عنوان caption",
    )
    storage_key: Optional[str] = Field(
        default=None,
        max_length=500,
        description="کلید ذخیره‌سازی فایل؛ برای VOICE و IMAGE و FILE الزامی است",
    )
    original_filename: Optional[str] = Field(
        default=None,
        max_length=255,
        description="نام فایل اصلی؛ برای VOICE و IMAGE و FILE الزامی است",
    )
    mime_type: Optional[str] = Field(
        default=None,
        max_length=120,
        description="نوع MIME؛ برای VOICE و IMAGE و FILE الزامی است",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        ge=1,
        description="اندازه فایل به بایت؛ برای VOICE و IMAGE و FILE الزامی است",
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="مدت صوت یا فیلم به ثانیه؛ اختیاری",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "content_kind_id",
        "file_size_bytes",
        "duration_seconds",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator(
        "content_kind",
        "text_body",
        "storage_key",
        "original_filename",
        "mime_type",
    )
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("content_kind")
    @classmethod
    def _kind_allowed(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        code = _KIND_ALIASES.get(value.upper() if value.isascii() else value)
        if code is None:
            raise ValueError("نوع محتوا باید TEXT، VOICE، IMAGE یا FILE باشد")
        return code

    @model_validator(mode="after")
    def _require_kind_and_payload(self):
        if self.content_kind_id is None and not self.content_kind:
            raise ValueError("نوع محتوا با شناسه یا نام لازم است")
        has_media = any(
            getattr(self, name) is not None for name in _MEDIA_FIELDS
        )
        if self.content_kind == "TEXT":
            if not self.text_body:
                raise ValueError("متن برای محتوای TEXT لازم است")
            if has_media:
                raise ValueError("محتوای متن نباید فایل داشته باشد")
        if self.content_kind in _MEDIA_KINDS:
            required = (
                self.storage_key,
                self.original_filename,
                self.mime_type,
                self.file_size_bytes,
            )
            if any(item is None for item in required):
                label = _MEDIA_LABELS[self.content_kind]
                raise ValueError(f"برای {label} کلید، نام فایل، نوع MIME و اندازه لازم است")
        return self


class GetContentInput(IdInput):
    """ورودی خواندن یک محتوا با شناسه."""


class DeleteContentInput(IdInput):
    """ورودی حذف نرم یک محتوا با شناسه."""


class ListContentsInput(PaginationInput):
    """ورودی فهرست محتواهای خود کاربر جاری."""
