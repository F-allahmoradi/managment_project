"""اسکیمای ورودی الگوی تکرار جلسه.

روز هفته ۰=شنبه تا ۶=جمعه، یا نام فارسی مثل چهارشنبه.
"""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.meeting.common import PaginationInput, reject_bool_for_int


class CreateMeetingScheduleInput(BaseModel):
    """ورودی ساخت الگوی تکرار. نوع از seed است مثل جلسه تیم."""

    meeting_type_id: Optional[int] = Field(default=None, ge=1)
    meeting_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل جلسه تیم یا مذاکره مدیران",
    )
    day_of_week: Optional[int] = Field(
        default=None,
        ge=0,
        le=6,
        description="۰=شنبه تا ۶=جمعه",
    )
    day_name: Optional[str] = Field(
        default=None,
        max_length=20,
        description="نام روز مثل چهارشنبه",
    )
    start_time: time = Field(description="ساعت شروع، مثلاً ۱۰:۰۰")
    duration_minutes: int = Field(default=60, ge=1, description="مدت جلسه به دقیقه")
    project_id: Optional[int] = Field(default=None, ge=1)
    is_active: bool = Field(default=True)
    effective_from: Optional[date] = Field(default=None)
    effective_until: Optional[date] = Field(default=None)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("meeting_type_id", "day_of_week", "project_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def _reject_bool_for_duration(cls, value):
        return reject_bool_for_int(value)

    @field_validator("meeting_type", "day_name")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_type_and_day(self):
        if self.meeting_type_id is None and not self.meeting_type:
            raise ValueError("نوع جلسه با شناسه یا نام لازم است")
        if self.day_of_week is None and not self.day_name:
            raise ValueError("روز هفته با عدد یا نام لازم است")
        if (
            self.effective_until is not None
            and self.effective_from is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("پایان اعتبار نباید قبل از شروع باشد")
        return self


class GetMeetingScheduleInput(BaseModel):
    """ورودی خواندن یک الگوی جلسه با شناسه."""

    id: int = Field(ge=1, description="شناسه الگو در meeting_schedules")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class ListMeetingSchedulesInput(PaginationInput):
    """فهرست الگوهای جلسهٔ کاربر جاری."""

    project_id: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = Field(default=None)

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
