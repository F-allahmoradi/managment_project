"""اسکیمای ورودی و خروجی ابزارهای Role.

ستون‌های جدول roles: name، description، is_system_role، is_active.
نقش سیستمی از کلاینت ساخته نمی‌شود؛ seed دست‌نخورده می‌ماند.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateRoleInput(BaseModel):
    """ورودی ثبت یک نقش جدید در roles."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="نام نقش؛ الزامی، یکتا و غیرخالی",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح نقش؛ اختیاری",
    )
    is_active: bool = Field(
        default=True,
        description="فعال بودن نقش؛ پیش‌فرض true",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value


class GetRoleInput(IdInput):
    """ورودی خواندن یک نقش با شناسه."""


class ListRolesInput(PaginationInput):
    """ورودی فهرست نقش‌ها با صفحه‌بندی اختیاری."""


class UpdateRoleInput(BaseModel):
    """ورودی به‌روزرسانی یک نقش موجود.

    is_system_role از کلاینت پذیرفته نمی‌شود تا نقش seed عوض نشود.
    """

    id: int = Field(ge=1, description="شناسه نقش در roles")
    name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نقش؛ اگر بیاید نباید خالی باشد",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح نقش",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="فعال بودن نقش",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)

    @field_validator("name")
    @classmethod
    def _optional_name_not_empty(cls, value: Optional[str]) -> Optional[str]:
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


class DeleteRoleInput(GetRoleInput):
    """ورودی حذف یک نقش با شناسه."""
