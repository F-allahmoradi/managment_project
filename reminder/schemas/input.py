"""اسکیمای ورودی ابزارهای تعریف و ارسال یادآوری.

متن در message_template است. content_id و task_item_id از کلاینت
گرفته نمی‌شوند. گیرنده همان قانون پیام است: XOR روی هر ردیف.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def reject_bool_for_int(value):
    """True/False را به‌جای عدد صحیح نمی‌پذیرد."""
    if isinstance(value, bool):
        raise ValueError("باید عدد صحیح باشد نه بولین")
    return value


class PaginationInput(BaseModel):
    """صفحه‌بندی مشترک فهرست‌ها؛ سقف ۵۰."""

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="تعداد رکورد در هر صفحه؛ پیش‌فرض ۱۰، حداکثر ۵۰",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="تعداد رکورد ردشده از ابتدا؛ پیش‌فرض ۰",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("limit", "offset", mode="before")
    @classmethod
    def _reject_bool_for_page(cls, value):
        return reject_bool_for_int(value)


class CreateReminderInput(BaseModel):
    """ورودی تعریف یادآوری با حداقل یک گیرنده.

    target_user_id و target_external_contact_id اگر هر دو بیایند
    دو گیرندهٔ جدا ساخته می‌شوند، نه یک ردیف با هر دو فیلد.
    """

    title: str = Field(min_length=1, max_length=200, description="عنوان یادآوری")
    message_template: str = Field(
        min_length=1,
        description="متن یادآوری؛ در این گام الزامی است",
    )
    scheduled_at: datetime = Field(description="زمان برنامه‌ریزی‌شده")
    next_run_at: Optional[datetime] = Field(
        default=None,
        description="زمان اجرای بعدی؛ پیش‌فرض همان scheduled_at",
    )
    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="پروژه اختیاری",
    )
    reminder_type_id: Optional[int] = Field(default=None, ge=1)
    reminder_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل یک‌باره یا دوره‌ای",
    )
    frequency_id: Optional[int] = Field(default=None, ge=1)
    frequency: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام تکرار seed مثل یک‌باره یا هفتگی",
    )
    status_id: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام وضعیت seed؛ پیش‌فرض فعال",
    )
    target_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ کاربر سامانه؛ یک ردیف reminder_targets",
    )
    target_external_contact_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ مخاطب خارجی؛ یک ردیف جدا",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "project_id",
        "reminder_type_id",
        "frequency_id",
        "status_id",
        "target_user_id",
        "target_external_contact_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator(
        "title",
        "message_template",
        "reminder_type",
        "frequency",
        "status",
    )
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_lookups_and_target(self):
        if self.reminder_type_id is None and not self.reminder_type:
            raise ValueError("نوع یادآوری با شناسه یا نام لازم است")
        if self.frequency_id is None and not self.frequency:
            raise ValueError("تکرار یادآوری با شناسه یا نام لازم است")
        if (
            self.target_user_id is None
            and self.target_external_contact_id is None
        ):
            raise ValueError("حداقل یک گیرنده لازم است")
        return self


class GetReminderInput(BaseModel):
    """ورودی خواندن یک یادآوری با شناسه."""

    id: int = Field(ge=1, description="شناسه یادآوری در reminders")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class ListRemindersInput(PaginationInput):
    """فهرست یادآوری‌های قابل‌مشاهدهٔ کاربر جاری."""

    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط یادآوری‌های همین پروژه",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)


class UpdateReminderInput(BaseModel):
    """ورودی به‌روزرسانی تعریف یادآوری.

    project_id و created_by_user_id عوض نمی‌شوند.
    گیرنده‌ها در این ابزار عوض نمی‌شوند.
    """

    id: int = Field(ge=1, description="شناسه یادآوری در reminders")
    title: Optional[str] = Field(default=None, max_length=200)
    message_template: Optional[str] = Field(default=None)
    scheduled_at: Optional[datetime] = Field(default=None)
    next_run_at: Optional[datetime] = Field(default=None)
    reminder_type_id: Optional[int] = Field(default=None, ge=1)
    reminder_type: Optional[str] = Field(default=None, max_length=100)
    frequency_id: Optional[int] = Field(default=None, ge=1)
    frequency: Optional[str] = Field(default=None, max_length=100)
    status_id: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, max_length=100)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "id",
        "reminder_type_id",
        "frequency_id",
        "status_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "message_template", "reminder_type", "frequency", "status")
    @classmethod
    def _optional_text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_writable_field(self):
        values = self.model_dump(exclude={"id"})
        if not any(value is not None for value in values.values()):
            raise ValueError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
        return self


class ListFollowUpStatesInput(PaginationInput):
    """فهرست وضعیت پیگیری گیرنده‌های یک یادآوری."""

    reminder_id: int = Field(ge=1, description="شناسه یادآوری")

    @field_validator("reminder_id", mode="before")
    @classmethod
    def _reject_bool_for_reminder_id(cls, value):
        return reject_bool_for_int(value)


def validate_create_reminder(fields: dict) -> dict:
    """ورودی تعریف یادآوری را با اسکیما بررسی می‌کند."""
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        return CreateReminderInput(**payload).model_dump()

    return _run(fields)


def validate_get_reminder(reminder_id: int) -> int:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(value: int) -> int:
        return GetReminderInput(id=value).id

    return _run(reminder_id)


def validate_list_reminders(project_id=None, limit=None, offset=None) -> dict:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        return ListRemindersInput(**payload).model_dump()

    data = {}
    if project_id is not None:
        data["project_id"] = project_id
    if limit is not None:
        data["limit"] = limit
    if offset is not None:
        data["offset"] = offset
    return _run(data)


def validate_update_reminder(fields: dict) -> dict:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        parsed = UpdateReminderInput(**payload)
        dumped = parsed.model_dump()
        return {
            "id": dumped["id"],
            **{
                key: value
                for key, value in dumped.items()
                if key != "id" and value is not None
            },
        }

    return _run(fields)


class DispatchReminderInput(BaseModel):
    """ورودی ارسال یا تلاش مجدد یک یادآوری روی کانال INTERNAL."""

    reminder_id: int = Field(ge=1, description="شناسه یادآوری")
    target_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط همین کاربر گیرنده ارسال می‌شود",
    )
    target_external_contact_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط همین مخاطب خارجی ارسال می‌شود",
    )
    channel: str = Field(
        default="INTERNAL",
        max_length=20,
        description="کانال ارسال؛ در این گام فقط INTERNAL",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="کلید جلوگیری از ارسال تکراری؛ فقط با یک گیرنده",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "reminder_id",
        "target_user_id",
        "target_external_contact_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("channel")
    @classmethod
    def _channel_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _xor_optional_target(self):
        if (
            self.target_user_id is not None
            and self.target_external_contact_id is not None
        ):
            raise ValueError(
                "گیرنده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
            )
        if self.idempotency_key is not None and (
            self.target_user_id is None
            and self.target_external_contact_id is None
        ):
            raise ValueError(
                "کلید idempotency فقط وقتی مجاز است که یک گیرنده مشخص باشد"
            )
        return self


class ListExecutionLogsInput(PaginationInput):
    """فهرست لاگ ارسال یک یادآوری."""

    reminder_id: int = Field(ge=1, description="شناسه یادآوری")

    @field_validator("reminder_id", mode="before")
    @classmethod
    def _reject_bool_for_reminder_id(cls, value):
        return reject_bool_for_int(value)


def validate_list_follow_up_states(
    reminder_id: int,
    limit=None,
    offset=None,
) -> dict:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        return ListFollowUpStatesInput(**payload).model_dump()

    data = {"reminder_id": reminder_id}
    if limit is not None:
        data["limit"] = limit
    if offset is not None:
        data["offset"] = offset
    return _run(data)


def validate_dispatch_reminder(fields: dict) -> dict:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        parsed = DispatchReminderInput(**payload).model_dump()
        return {
            key: value
            for key, value in parsed.items()
            if value is not None or key == "channel"
        }

    return _run(fields)


def validate_list_execution_logs(
    reminder_id: int,
    limit=None,
    offset=None,
) -> dict:
    from logging_module import logged_step

    @logged_step("validate")
    def _run(payload: dict) -> dict:
        return ListExecutionLogsInput(**payload).model_dump()

    data = {"reminder_id": reminder_id}
    if limit is not None:
        data["limit"] = limit
    if offset is not None:
        data["offset"] = offset
    return _run(data)
