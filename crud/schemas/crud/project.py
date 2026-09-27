"""اسکیمای ورودی ابزارهای Project.

ستون‌های جدول projects: name، description، نوع، وضعیت، تاریخ شروع و پایان.
created_by از کاربر جاری می‌آید؛ از کلاینت پذیرفته نمی‌شود.
نوع و وضعیت lookup هستند؛ شناسه یا نام seed مثل نرم‌افزاری قبول است.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


def _optional_date(value):
    """رشتهٔ ISO یا date را می‌پذیرد؛ رشتهٔ خالی را رد می‌کند."""
    if value is None or value == "":
        return None
    return value


class CreateProjectInput(BaseModel):
    """ورودی ثبت یک پروژه جدید در projects."""

    name: str = Field(
        min_length=1,
        max_length=200,
        description="نام پروژه؛ الزامی و غیرخالی",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح پروژه؛ اختیاری",
    )
    project_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در project_types",
    )
    project_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل نرم‌افزاری",
    )
    project_status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه وضعیت در project_statuses",
    )
    project_status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام وضعیت seed مثل در حال اجرا",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="تاریخ شروع؛ اختیاری",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="تاریخ پایان؛ اگر بیاید نباید قبل از شروع باشد",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name", "project_type", "project_status")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("project_type_id", "project_status_id", mode="before")
    @classmethod
    def _reject_bool_for_lookup_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _parse_optional_date(cls, value):
        return _optional_date(value)

    @model_validator(mode="after")
    def _require_type_and_status(self):
        if self.project_type_id is None and not self.project_type:
            raise ValueError("نوع پروژه با شناسه یا نام لازم است")
        if self.project_status_id is None and not self.project_status:
            raise ValueError("وضعیت پروژه با شناسه یا نام لازم است")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("تاریخ پایان نباید قبل از تاریخ شروع باشد")
        return self


class GetProjectInput(IdInput):
    """ورودی خواندن یک پروژه با شناسه."""


class ListProjectsInput(PaginationInput):
    """ورودی فهرست پروژه‌های قابل‌مشاهدهٔ کاربر جاری."""


class UpdateProjectInput(BaseModel):
    """ورودی به‌روزرسانی یک پروژه موجود.

    created_by عوض نمی‌شود. حداقل یک فیلد قابل‌نوشتن لازم است.
    """

    id: int = Field(ge=1, description="شناسه پروژه در projects")
    name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="نام پروژه؛ اگر بیاید نباید خالی باشد",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح پروژه",
    )
    project_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در project_types",
    )
    project_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل نرم‌افزاری",
    )
    project_status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه وضعیت در project_statuses",
    )
    project_status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام وضعیت seed مثل در حال اجرا",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="تاریخ شروع",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="تاریخ پایان",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("id", "project_type_id", "project_status_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("name", "project_type", "project_status")
    @classmethod
    def _optional_text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _parse_optional_date(cls, value):
        return _optional_date(value)

    @model_validator(mode="after")
    def _require_writable_field(self):
        values = self.model_dump(exclude={"id"})
        if not any(value is not None for value in values.values()):
            raise ValueError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("تاریخ پایان نباید قبل از تاریخ شروع باشد")
        return self
