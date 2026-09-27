"""اسکیمای ورودی ابزارهای ExternalContact.

مخاطب خارجی وارد پنل نمی‌شود؛ فقط پیام یا یادآوری می‌گیرد.
عضو جدول users نیست.
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    return value


class CreateExternalContactInput(BaseModel):
    """ورودی ثبت یک مخاطب خارج از سامانه."""

    name: str = Field(
        min_length=1,
        max_length=200,
        description="نام مخاطب؛ الزامی و غیرخالی",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="شماره تلفن یکتا؛ اختیاری",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="ایمیل یکتا؛ اختیاری",
    )
    telegram_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="شناسه تلگرام یکتا؛ اختیاری",
    )
    is_active: bool = Field(
        default=True,
        description="فعال بودن مخاطب؛ پیش‌فرض true",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("phone", "telegram_id")
    @classmethod
    def _optional_text(cls, value: Optional[str]) -> Optional[str]:
        return _blank_to_none(value)

    @field_validator("email")
    @classmethod
    def _optional_email(cls, value: Optional[str]) -> Optional[str]:
        value = _blank_to_none(value)
        if value is None:
            return None
        if not _EMAIL_RE.match(value):
            raise ValueError("قالب ایمیل نامعتبر است")
        return value


class GetExternalContactInput(IdInput):
    """ورودی خواندن یک مخاطب خارجی با شناسه."""


class ListExternalContactsInput(PaginationInput):
    """فهرست مخاطبان خارج از سامانه."""
