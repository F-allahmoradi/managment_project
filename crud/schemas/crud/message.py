"""اسکیمای ورودی ابزارهای Message.

متن در text است. content_id در این گام از کلاینت گرفته نمی‌شود.
گیرندهٔ کاربر و مخاطب خارجی دو ردیف جدا در message_recipientsاند.
پروژه بستر ارسال است؛ وظیفه اختیاری است. ژانر از تحلیل می‌آید.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateMessageInput(BaseModel):
    """ورودی ارسال پیام متنی داخل گفتگو.

    recipient_user_id و recipient_external_contact_id اگر هر دو بیایند
    دو گیرندهٔ جدا ساخته می‌شوند، نه یک ردیف با هر دو فیلد.
    حداقل یکی لازم است.
    در گفتگوی پروژه task_id اختیاری است و اگر بیاید باید همان پروژه باشد.
    گفتگوی خصوصی نباید task_id داشته باشد.
    """

    chat_id: int = Field(ge=1, description="شناسه گفتگو")
    task_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="وظیفهٔ اختیاری همان پروژه؛ در گفتگوی خصوصی خالی است",
    )
    text: str = Field(
        min_length=1,
        description="متن پیام؛ در این گام الزامی است",
    )
    recipient_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ کاربر سامانه؛ یک ردیف message_recipients",
    )
    recipient_external_contact_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ مخاطب خارجی؛ یک ردیف جدا",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "chat_id",
        "task_id",
        "recipient_user_id",
        "recipient_external_contact_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("text")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_recipient(self):
        if (
            self.recipient_user_id is None
            and self.recipient_external_contact_id is None
        ):
            raise ValueError("حداقل یک گیرنده لازم است")
        return self


class GetMessageInput(IdInput):
    """ورودی خواندن یک پیام با شناسه."""


class ListMessagesInput(PaginationInput):
    """فهرست پیام‌های گفتگوهایی که کاربر عضوشان است."""

    chat_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط پیام‌های همین گفتگو",
    )

    @field_validator("chat_id", mode="before")
    @classmethod
    def _reject_bool_for_chat_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
