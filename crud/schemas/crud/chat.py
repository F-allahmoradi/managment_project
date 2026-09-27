"""اسکیمای ورودی ابزارهای Chat.

گفتگوی خصوصی project_id ندارد. گفتگوی پروژه باید به پروژه وصل باشد.
سازنده همان لحظه عضو chat_members می‌شود.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateChatInput(BaseModel):
    """ورودی ساخت یک گفتگو؛ خصوصی یا روی پروژه."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="عنوان گفتگو؛ الزامی و غیرخالی",
    )
    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه پروژه؛ برای گفتگوی خصوصی خالی است",
    )
    chat_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در chat_types",
    )
    chat_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل گفتگوی پروژه",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("project_id", "chat_type_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "chat_type")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_chat_type(self):
        if self.chat_type_id is None and not self.chat_type:
            raise ValueError("نوع گفتگو با شناسه یا نام لازم است")
        return self


class GetChatInput(IdInput):
    """ورودی خواندن یک گفتگو با شناسه."""


class ListChatsInput(PaginationInput):
    """فهرست گفتگوهایی که کاربر عضوشان است."""

    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط گفتگوهای همین پروژه",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
