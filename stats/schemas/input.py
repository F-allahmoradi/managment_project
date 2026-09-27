"""اسکیمای ورودی ابزارهای آمار فقط‌خواندنی."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from logging_module import logged_step


def reject_bool_for_int(value):
    """True/False را به‌جای عدد صحیح نمی‌پذیرد."""
    if isinstance(value, bool):
        raise ValueError("باید عدد صحیح باشد نه بولین")
    return value


class PaginationInput(BaseModel):
    """صفحه‌بندی فهرست آمار؛ سقف ۵۰ مثل CRUD است."""

    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    model_config = ConfigDict(extra="forbid")

    @field_validator("limit", "offset", mode="before")
    @classmethod
    def _reject_bool_for_page(cls, value):
        return reject_bool_for_int(value)


class ProjectIdInput(BaseModel):
    """شناسه پروژه برای آمار یک پروژه."""

    project_id: int = Field(ge=1, description="شناسه پروژه؛ الزامی")
    model_config = ConfigDict(extra="forbid")

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool(cls, value):
        return reject_bool_for_int(value)


class OptionalProjectInput(BaseModel):
    """فیلتر اختیاری پروژه برای آمار تجمیعی."""

    project_id: Optional[int] = Field(default=None, ge=1)
    model_config = ConfigDict(extra="forbid")

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool(cls, value):
        if value is None:
            return value
        return reject_bool_for_int(value)


class OptionalProjectPageInput(PaginationInput):
    """صفحه‌بندی با فیلتر اختیاری پروژه."""

    project_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_project(cls, value):
        if value is None:
            return value
        return reject_bool_for_int(value)


class MemberFilterInput(OptionalProjectInput):
    """فیلتر اختیاری پروژه و عضو."""

    user_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("user_id", mode="before")
    @classmethod
    def _reject_bool_user(cls, value):
        if value is None:
            return value
        return reject_bool_for_int(value)


class FollowUpFilterInput(OptionalProjectPageInput):
    """فیلتر پیگیری با حداقل شمار اختیاری."""

    min_count: Optional[int] = Field(default=None, ge=0)

    @field_validator("min_count", mode="before")
    @classmethod
    def _reject_bool_count(cls, value):
        if value is None:
            return value
        return reject_bool_for_int(value)


class TransactionFilterInput(OptionalProjectInput):
    """فیلتر خلاصه تراکنش با حساب اختیاری."""

    account_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("account_id", mode="before")
    @classmethod
    def _reject_bool_account(cls, value):
        if value is None:
            return value
        return reject_bool_for_int(value)


def validate_project_id(project_id: int) -> int:
    """شناسه پروژه را بررسی می‌کند."""
    return ProjectIdInput(project_id=project_id).project_id


def validate_optional_project(project_id=None) -> dict:
    """فیلتر اختیاری پروژه را بررسی می‌کند."""
    return OptionalProjectInput(project_id=project_id).model_dump()


def validate_optional_project_page(project_id=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر پروژه را بررسی می‌کند."""
    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return OptionalProjectPageInput(**payload).model_dump()


def validate_pagination(limit=None, offset=None) -> dict:
    """فقط صفحه‌بندی را بررسی می‌کند."""
    payload = {}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return PaginationInput(**payload).model_dump()


def validate_member_filter(project_id=None, user_id=None) -> dict:
    """فیلتر عضو و پروژه را بررسی می‌کند."""
    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if user_id is not None:
        payload["user_id"] = user_id
    return MemberFilterInput(**payload).model_dump()


def validate_follow_up_filter(
    project_id=None,
    min_count=None,
    limit=None,
    offset=None,
) -> dict:
    """فیلتر شمار پیگیری را بررسی می‌کند."""
    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if min_count is not None:
        payload["min_count"] = min_count
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return FollowUpFilterInput(**payload).model_dump()


def validate_transaction_filter(project_id=None, account_id=None) -> dict:
    """فیلتر خلاصه تراکنش را بررسی می‌کند."""
    payload = {}
    if project_id is not None:
        payload["project_id"] = project_id
    if account_id is not None:
        payload["account_id"] = account_id
    return TransactionFilterInput(**payload).model_dump()


validate_project_id = logged_step("validate")(validate_project_id)
validate_optional_project = logged_step("validate")(validate_optional_project)
validate_optional_project_page = logged_step("validate")(
    validate_optional_project_page
)
validate_pagination = logged_step("validate")(validate_pagination)
validate_member_filter = logged_step("validate")(validate_member_filter)
validate_follow_up_filter = logged_step("validate")(validate_follow_up_filter)
validate_transaction_filter = logged_step("validate")(validate_transaction_filter)
