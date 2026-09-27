"""اسکیمای ورودی و خروجی ابزارهای Permission.

هویت مجوز Resource + Action است، مثل User/Create.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.crud.common import PaginationInput, reject_bool_for_int


class CreatePermissionInput(BaseModel):
    """ورودی ثبت یک مجوز ریز در permissions."""

    name: str = Field(
        min_length=1,
        max_length=150,
        description="نام نمایشی مجوز؛ یکتا",
    )
    resource: str = Field(
        min_length=1,
        max_length=80,
        description="موجودیت مثل User یا Task",
    )
    action: str = Field(
        min_length=1,
        max_length=40,
        description="عمل مثل Create یا Read",
    )
    description: Optional[str] = Field(
        default=None,
        description="توضیح مجوز؛ اختیاری",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name", "resource", "action")
    @classmethod
    def _required_text_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value


class ListPermissionsInput(PaginationInput):
    """ورودی فهرست مجوزها با صفحه‌بندی اختیاری."""
