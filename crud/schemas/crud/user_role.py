"""اسکیمای اتصال نقش به کاربر در user_roles."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateUserRoleInput(BaseModel):
    """ورودی دادن یک نقش به یک کاربر."""

    user_id: int = Field(ge=1, description="شناسه کاربر")
    role_id: int = Field(ge=1, description="شناسه نقش")
    model_config = ConfigDict(extra="forbid")

    @field_validator("user_id", "role_id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class DeleteUserRoleInput(IdInput):
    """ورودی گرفتن نقش از کاربر با شناسه ردیف اتصال."""


class ListUserRolesInput(PaginationInput):
    """فهرست نقش‌های یک کاربر؛ user_id اختیاری است."""

    user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط نقش‌های همین کاربر",
    )

    @field_validator("user_id", mode="before")
    @classmethod
    def _reject_bool_for_user_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
