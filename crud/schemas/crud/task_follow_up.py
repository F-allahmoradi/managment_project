"""اسکیمای ورودی ابزارهای TaskFollowUp.

پیگیری یک رخداد جدا روی همان وظیفه است: کی، چه نوعی، نتیجه، بعدی.
وضعیت اینجا نتیجه پیگیری است (منتظر پاسخ)، نه وضعیت خود کار.
task_item_id در این گام پذیرفته نمی‌شود.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


def _optional_datetime(value):
    """رشتهٔ ISO یا datetime را می‌پذیرد؛ تاریخ خالص را به نیمه‌شب می‌برد."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return value


class CreateTaskFollowUpInput(BaseModel):
    """ورودی ثبت یک پیگیری روی یک وظیفه."""

    task_id: int = Field(ge=1, description="شناسه همان وظیفه")
    note: str = Field(
        min_length=1,
        description="متن پیگیری؛ بدون محتوا الزامی است",
    )
    follow_up_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در follow_up_types",
    )
    follow_up_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل تماس یا پیام",
    )
    status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نتیجه در task_follow_up_statuses",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نتیجه seed مثل منتظر پاسخ",
    )
    follow_up_date: Optional[datetime] = Field(
        default=None,
        description="زمان این پیگیری؛ پیش‌فرض الان",
    )
    next_follow_up_date: Optional[datetime] = Field(
        default=None,
        description="زمان پیگیری بعدی؛ اختیاری",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("task_id", "follow_up_type_id", "status_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("note", "follow_up_type", "status")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("follow_up_date", "next_follow_up_date", mode="before")
    @classmethod
    def _parse_optional_datetime(cls, value):
        return _optional_datetime(value)

    @model_validator(mode="after")
    def _require_type_and_status(self):
        if self.follow_up_type_id is None and not self.follow_up_type:
            raise ValueError("نوع پیگیری با شناسه یا نام لازم است")
        if self.status_id is None and not self.status:
            raise ValueError("نتیجه پیگیری با شناسه یا نام لازم است")
        return self


class GetTaskFollowUpInput(IdInput):
    """ورودی خواندن یک پیگیری با شناسه."""


class ListTaskFollowUpsInput(PaginationInput):
    """فهرست پیگیری‌های یک وظیفه."""

    task_id: int = Field(ge=1, description="شناسه همان وظیفه")

    @field_validator("task_id", mode="before")
    @classmethod
    def _reject_bool_for_task_id(cls, value):
        return reject_bool_for_int(value)
