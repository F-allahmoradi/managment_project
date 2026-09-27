"""اسکیمای ورودی نمونهٔ جلسه: ساخت، فهرست، خواندن، لغو، تولید از الگو."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.meeting.common import PaginationInput, reject_bool_for_int

_VISIBILITY = frozenset({"PRIVATE", "RESTRICTED", "PROJECT"})


class CreateMeetingInput(BaseModel):
    """ورودی ساخت یک جلسه مشخص. وضعیت همیشه برنامه‌ریزی شده است."""

    title: str = Field(min_length=1, max_length=200, description="عنوان جلسه")
    scheduled_at: datetime = Field(description="شروع برنامه‌ریزی‌شده")
    meeting_type_id: Optional[int] = Field(default=None, ge=1)
    meeting_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل جلسه تیم یا مذاکره خارجی",
    )
    duration_minutes: int = Field(default=60, ge=1)
    project_id: Optional[int] = Field(default=None, ge=1)
    schedule_id: Optional[int] = Field(default=None, ge=1)
    visibility: str = Field(default="PRIVATE", description="PRIVATE یا RESTRICTED یا PROJECT")
    location: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "meeting_type_id",
        "duration_minutes",
        "project_id",
        "schedule_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "meeting_type", "location", "visibility")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("visibility")
    @classmethod
    def _visibility_allowed(cls, value: str) -> str:
        upper = value.upper()
        if upper not in _VISIBILITY:
            raise ValueError("visibility باید PRIVATE یا RESTRICTED یا PROJECT باشد")
        return upper

    @model_validator(mode="after")
    def _require_type_and_project_visibility(self):
        if self.meeting_type_id is None and not self.meeting_type:
            raise ValueError("نوع جلسه با شناسه یا نام لازم است")
        if self.visibility == "PROJECT" and self.project_id is None:
            raise ValueError("visibility برابر PROJECT بدون پروژه مجاز نیست")
        return self


class GetMeetingInput(BaseModel):
    """ورودی خواندن یک جلسه با شناسه."""

    id: int = Field(ge=1, description="شناسه جلسه در meetings")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class ListMeetingsInput(PaginationInput):
    """فهرست جلسات قابل‌مشاهدهٔ کاربر جاری."""

    project_id: Optional[int] = Field(default=None, ge=1)
    status_id: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, max_length=100)

    @field_validator("project_id", "status_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("status")
    @classmethod
    def _status_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value


class CancelMeetingInput(BaseModel):
    """ورودی لغو یک جلسه برنامه‌ریزی‌شده."""

    id: int = Field(ge=1, description="شناسه جلسه در meetings")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class GenerateMeetingsInput(BaseModel):
    """ورودی چیدن نمونه از روی الگو برای یک هفته."""

    schedule_id: int = Field(ge=1, description="شناسه الگوی meeting_schedules")
    weeks_ahead: int = Field(
        default=1,
        ge=0,
        le=12,
        description="۰ همین هفته، ۱ هفتهٔ بعد؛ پیش‌فرض ۱",
    )
    title: Optional[str] = Field(default=None, max_length=200)
    visibility: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("schedule_id", "weeks_ahead", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        return reject_bool_for_int(value)

    @field_validator("title", "visibility")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("visibility")
    @classmethod
    def _visibility_allowed(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        upper = value.upper()
        if upper not in _VISIBILITY:
            raise ValueError("visibility باید PRIVATE یا RESTRICTED یا PROJECT باشد")
        return upper


class RecordMeetingInput(BaseModel):
    """ورودی وصل کردن محتوای ضبط به جلسه."""

    id: int = Field(ge=1, description="شناسه جلسه در meetings")
    content_id: int = Field(ge=1, description="شناسه محتوا در contents")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", "content_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        return reject_bool_for_int(value)


class SyncMeetingInput(BaseModel):
    """ورودی همگام‌سازی خروجی جلسه به پروژه.

    متن از contents یا notes می‌آید. NLP استخراج نمی‌کند.
    """

    id: int = Field(ge=1, description="شناسه جلسه در meetings")
    confirm: bool = Field(
        default=False,
        description="برای مذاکره خارجی/حقوقی یا RESTRICTED لازم است",
    )
    notes: Optional[str] = Field(
        default=None,
        description="یادداشت دستی اگر text_body خالی باشد",
    )
    decision_title: Optional[str] = Field(default=None, max_length=200)
    decision_description: Optional[str] = Field(default=None)
    task_title: Optional[str] = Field(default=None, max_length=200)
    assigned_to_user_id: Optional[int] = Field(default=None, ge=1)
    task_id: Optional[int] = Field(default=None, ge=1)
    chat_id: Optional[int] = Field(default=None, ge=1)
    message_text: Optional[str] = Field(default=None)
    recipient_user_id: Optional[int] = Field(default=None, ge=1)
    recipient_external_contact_id: Optional[int] = Field(default=None, ge=1)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "id",
        "assigned_to_user_id",
        "task_id",
        "chat_id",
        "recipient_user_id",
        "recipient_external_contact_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator(
        "notes",
        "decision_title",
        "decision_description",
        "task_title",
        "message_text",
    )
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value
