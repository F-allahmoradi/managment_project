"""اسکیمای ورودی ابزارهای TaskItem.

فقط مسئول همان Task زیرکار می‌سازد، ویرایش می‌کند یا تیک می‌زند.
یادآوری از start_date / end_date در این گام ساخته نمی‌شود.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, reject_bool_for_int


def _optional_date(value):
    """رشتهٔ ISO یا date را می‌پذیرد؛ رشتهٔ خالی را رد می‌کند."""
    if value is None or value == "":
        return None
    return value


class CreateTaskItemInput(BaseModel):
    """ورودی ثبت یک زیرکار در task_items."""

    task_id: int = Field(ge=1, description="شناسه وظیفهٔ والد در tasks")
    title: str = Field(
        min_length=1,
        max_length=200,
        description="عنوان زیرکار؛ الزامی و غیرخالی",
    )
    parent_item_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="زیرکار والد؛ خالی یعنی سطح اول همان وظیفه",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح زیرکار؛ اختیاری",
    )
    sort_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="ترتیب میان خواهرها؛ اگر نیاید بعدیِ همان سطح است",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="شروع برنامه‌ریزی‌شده؛ یادآوری خودکار ساخته نمی‌شود",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="مهلت زیرکار؛ یادآوری خودکار ساخته نمی‌شود",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "task_id",
        "parent_item_id",
        "sort_order",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _parse_optional_date(cls, value):
        return _optional_date(value)

    @model_validator(mode="after")
    def _require_dates_order(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("پایان زیرکار نباید قبل از شروع باشد")
        return self


class ListTaskItemsInput(BaseModel):
    """فهرست/درخت زیرکارهای یک وظیفه."""

    task_id: int = Field(ge=1, description="شناسه وظیفه در tasks")
    model_config = ConfigDict(extra="forbid")

    @field_validator("task_id", mode="before")
    @classmethod
    def _reject_bool_for_task_id(cls, value):
        return reject_bool_for_int(value)


class UpdateTaskItemInput(BaseModel):
    """ورودی به‌روزرسانی عنوان، ترتیب یا تاریخ زیرکار.

    تیک زدن مال complete_task_item است. task_id عوض نمی‌شود.
    """

    id: int = Field(ge=1, description="شناسه زیرکار در task_items")
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="عنوان زیرکار",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح زیرکار",
    )
    sort_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="ترتیب میان خواهرها",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="شروع برنامه‌ریزی‌شده",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="مهلت زیرکار",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("id", "sort_order", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title")
    @classmethod
    def _optional_title_not_empty(cls, value: Optional[str]) -> Optional[str]:
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
            raise ValueError("پایان زیرکار نباید قبل از شروع باشد")
        return self


class CompleteTaskItemInput(BaseModel):
    """ورودی تیک زدن یا برداشتن تیک یک زیرکار."""

    id: int = Field(ge=1, description="شناسه زیرکار در task_items")
    is_completed: bool = Field(
        default=True,
        description="true یعنی تیک؛ false یعنی برداشتن تیک",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class DeleteTaskItemInput(IdInput):
    """ورودی حذف یک زیرکار؛ فرزندها با CASCADE پاک می‌شوند."""
