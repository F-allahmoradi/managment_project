"""مدل اعتبارسنجی ورودی استخراج زبانی."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SOURCE_TYPES = ("meeting", "message")


class ExtractNlpInput(BaseModel):
    """ورودی استخراج: متن آزاد یا شناسهٔ منبع خام.

    اگر source_type و source_id بیاید، متن از جدول عملیاتی خوانده می‌شود.
    context فقط برای رفع ارجاع است؛ شاهد باید از خود متن باشد.
    """

    text: Optional[str] = Field(
        default=None,
        description="متن جلسه یا پیام؛ اگر منبع باشد لازم نیست",
    )
    source_type: Optional[str] = Field(
        default=None,
        description="نوع منبع؛ meeting یا message",
    )
    source_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه ردیف منبع در جدول عملیاتی",
    )
    context: Optional[str] = Field(
        default=None,
        description="جملات قبل/بعد برای رفع ارجاع؛ شاهد از متن اصلی است",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("source_id", mode="before")
    @classmethod
    def _reject_bool_for_int(cls, value):
        if isinstance(value, bool):
            raise ValueError("باید عدد صحیح باشد نه بولین")
        return value

    @field_validator("source_type")
    @classmethod
    def _allowed_source_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        code = value.strip().lower()
        if code not in _SOURCE_TYPES:
            raise ValueError("source_type باید meeting یا message باشد")
        return code

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value:
            raise ValueError("متن نمی‌تواند خالی باشد")
        return value

    @field_validator("context")
    @classmethod
    def _context_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value:
            return None
        return value

    @model_validator(mode="after")
    def _require_text_or_source(self):
        has_text = bool(self.text)
        has_source = self.source_type is not None or self.source_id is not None
        if has_text and has_source:
            raise ValueError("متن آزاد و شناسه منبع را با هم نفرستید")
        if has_source and (self.source_type is None or self.source_id is None):
            raise ValueError("source_type و source_id هر دو لازم‌اند")
        if not has_text and not has_source:
            raise ValueError("متن یا شناسه منبع لازم است")
        return self
