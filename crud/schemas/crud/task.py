"""اسکیمای ورودی ابزارهای Task.

کار با پیگیری یکی نیست. اولویت فوریت است؛ اهمیت اثر روی نتیجه است.
created_by_user_id از کاربر جاری می‌آید. مسئول اگر بیاید باید
عضو فعال همان پروژه باشد — این قید در سرویس است، نه در اسکیما.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


def _optional_date(value):
    """رشتهٔ ISO یا date را می‌پذیرد؛ رشتهٔ خالی را رد می‌کند."""
    if value is None or value == "":
        return None
    return value


def _optional_datetime(value):
    """رشتهٔ ISO یا datetime را می‌پذیرد؛ تاریخ خالص را به نیمه‌شب می‌برد."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return value


class CreateTaskInput(BaseModel):
    """ورودی ثبت یک وظیفه جدید در tasks."""

    project_id: int = Field(ge=1, description="شناسه پروژه؛ الزامی")
    title: str = Field(
        min_length=1,
        max_length=200,
        description="عنوان کار؛ الزامی و غیرخالی",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح کار؛ اختیاری",
    )
    assigned_to_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="مسئول؛ باید عضو فعال همین پروژه باشد",
    )
    status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه وضعیت در task_statuses",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام وضعیت seed مثل شروع نشده",
    )
    priority_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه فوریت در task_priorities",
    )
    priority: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام فوریت seed مثل کم یا فوری",
    )
    importance_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه اهمیت در task_importances",
    )
    importance: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام اهمیت seed مثل کم یا حیاتی",
    )
    importance_percent: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="درصد اهمیت اختیاری؛ ۰ تا ۱۰۰",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="تاریخ شروع برنامه‌ریزی‌شده",
    )
    due_date: Optional[date] = Field(
        default=None,
        description="مهلت؛ اگر بیاید نباید قبل از شروع باشد",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "project_id",
        "assigned_to_user_id",
        "status_id",
        "priority_id",
        "importance_id",
        "importance_percent",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "status", "priority", "importance")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("start_date", "due_date", mode="before")
    @classmethod
    def _parse_optional_date(cls, value):
        return _optional_date(value)

    @model_validator(mode="after")
    def _require_lookups_and_dates(self):
        if self.status_id is None and not self.status:
            raise ValueError("وضعیت کار با شناسه یا نام لازم است")
        if self.priority_id is None and not self.priority:
            raise ValueError("اولویت کار با شناسه یا نام لازم است")
        if self.importance_id is None and not self.importance:
            raise ValueError("اهمیت کار با شناسه یا نام لازم است")
        if (
            self.start_date is not None
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError("مهلت نباید قبل از تاریخ شروع باشد")
        return self


class GetTaskInput(IdInput):
    """ورودی خواندن یک وظیفه با شناسه."""


class ListTasksInput(PaginationInput):
    """فهرست وظایف پروژه‌هایی که کاربر عضو فعال‌شان است."""

    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط وظایف همین پروژه",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)


class UpdateTaskInput(BaseModel):
    """ورودی به‌روزرسانی یک وظیفه موجود.

    project_id و created_by_user_id عوض نمی‌شوند.
    عوض کردن وضعیت ردیف پیگیری نمی‌سازد.
    """

    id: int = Field(ge=1, description="شناسه وظیفه در tasks")
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="عنوان کار",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح کار",
    )
    assigned_to_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="مسئول جدید؛ باید عضو فعال همین پروژه باشد",
    )
    status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه وضعیت در task_statuses",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام وضعیت seed مثل در حال انجام",
    )
    priority_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه فوریت در task_priorities",
    )
    priority: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام فوریت seed مثل فوری",
    )
    importance_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه اهمیت در task_importances",
    )
    importance: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام اهمیت seed مثل حیاتی",
    )
    importance_percent: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="درصد اهمیت؛ ۰ تا ۱۰۰",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="تاریخ شروع",
    )
    due_date: Optional[date] = Field(
        default=None,
        description="مهلت",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="زمان تکمیل؛ اختیاری",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "id",
        "assigned_to_user_id",
        "status_id",
        "priority_id",
        "importance_id",
        "importance_percent",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "status", "priority", "importance")
    @classmethod
    def _optional_text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("start_date", "due_date", mode="before")
    @classmethod
    def _parse_optional_date(cls, value):
        return _optional_date(value)

    @field_validator("completed_at", mode="before")
    @classmethod
    def _parse_optional_datetime(cls, value):
        return _optional_datetime(value)

    @model_validator(mode="after")
    def _require_writable_field(self):
        values = self.model_dump(exclude={"id"})
        if not any(value is not None for value in values.values()):
            raise ValueError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
        if (
            self.start_date is not None
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError("مهلت نباید قبل از تاریخ شروع باشد")
        return self
