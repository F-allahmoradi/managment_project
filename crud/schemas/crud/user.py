"""اسکیمای ورودی و خروجی ابزارهای User.

ستون‌های جدول users: نام، نام خانوادگی، تلفن، ایمیل، نام کاربری،
رمز، is_active. id و created_at و password_hash از کلاینت گرفته نمی‌شوند.
رمز خام فقط در ورودی ساخت و به‌روزرسانی است؛ در پاسخ نمی‌آید.
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 128


class CreateUserInput(BaseModel):
    """ورودی ثبت یک کاربر جدید در users.

    ورودی:
        فیلدهای اجباری نام و نام خانوادگی و نام کاربری و رمز.
        تلفن و ایمیل و is_active اختیاری‌اند.
    خروجی:
        نمونه معتبر پس از trim و طول و قالب ایمیل.
    فراخوانی‌ها:
        اعتبارسنجی Pydantic.
    علت:
        ابزار MCP قبل از INSERT باید ورودی نامعتبر را با INVALID_INPUT رد کند.
    """

    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="نام؛ الزامی و غیرخالی",
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="نام خانوادگی؛ الزامی و غیرخالی",
    )
    username: str = Field(
        min_length=1,
        max_length=80,
        description="نام کاربری یکتا؛ الزامی و غیرخالی",
    )
    password: str = Field(
        min_length=_PASSWORD_MIN_LENGTH,
        max_length=_PASSWORD_MAX_LENGTH,
        description="رمز خام؛ حداقل ۸ نویسه؛ در دیتابیس هش می‌شود",
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
    is_active: bool = Field(
        default=True,
        description="فعال بودن حساب؛ پیش‌فرض true",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("first_name", "last_name", "username")
    @classmethod
    def _required_text_not_empty(cls, value: str) -> str:
        """رشتهٔ اجباری را پس از trim رد می‌کند اگر خالی باشد."""
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("phone")
    @classmethod
    def _optional_phone_not_empty(cls, value: Optional[str]) -> Optional[str]:
        """تلفن داده‌شده را اگر خالی باشد رد می‌کند."""
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("email")
    @classmethod
    def _optional_email_valid(cls, value: Optional[str]) -> Optional[str]:
        """ایمیل داده‌شده را اگر خالی یا بی‌قالب باشد رد می‌کند."""
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        if not _EMAIL_RE.match(value):
            raise ValueError("قالب ایمیل معتبر نیست")
        return value.lower()


class CreateUserOutput(BaseModel):
    """خروجی موفق ثبت کاربر جدید."""

    status: str = Field(default="success", description="همیشه success")
    message: str = Field(description="پیام خوانا برای کلاینت")
    id: int = Field(description="شناسه کاربر تازه‌ثبت‌شده در users")
    model_config = ConfigDict(extra="forbid")


class GetUserInput(IdInput):
    """ورودی خواندن یک کاربر با شناسه."""


class UserPublicFields(BaseModel):
    """ستون‌های قابل‌نمایش کاربر؛ بدون password و password_hash."""

    id: int = Field(description="شناسه کاربر در users")
    first_name: Optional[str] = Field(default=None, description="نام")
    last_name: Optional[str] = Field(default=None, description="نام خانوادگی")
    phone: Optional[str] = Field(default=None, description="شماره تلفن")
    email: Optional[str] = Field(default=None, description="ایمیل")
    username: Optional[str] = Field(default=None, description="نام کاربری")
    is_active: Optional[bool] = Field(default=None, description="فعال بودن حساب")
    created_at: Optional[str] = Field(default=None, description="زمان ایجاد")


class GetUserOutput(UserPublicFields):
    """خروجی موفق خواندن یک کاربر."""

    status: str = Field(default="success", description="همیشه success")
    message: str = Field(description="پیام خوانا برای کلاینت")


class ListUsersInput(PaginationInput):
    """ورودی فهرست کاربران با صفحه‌بندی اختیاری.

    سقف ۵۰ با policies.yaml یکی است؛ بیش از آن INVALID_INPUT است.
    """


class ListUsersOutput(BaseModel):
    """خروجی موفق فهرست کاربران."""

    status: str = Field(default="success", description="همیشه success")
    message: str = Field(description="پیام خوانا برای کلاینت")
    records: list = Field(
        description="لیست کاربران بدون password_hash",
    )
    limit: int = Field(description="تعداد رکورد درخواستی پس از صفحه‌بندی")
    offset: int = Field(description="جابه‌جایی اعمال‌شده")
    model_config = ConfigDict(extra="forbid")


class UpdateUserInput(BaseModel):
    """ورودی به‌روزرسانی یک کاربر موجود در users.

    ورودی:
        id اجباری. بقیه ستون‌های قابل‌نوشتن اختیاری‌اند.
        حداقل یک فیلد قابل‌نوشتن باید بیاید.
    خروجی:
        نمونه معتبر با حداقل یک فیلد غیرتهی غیر از id.
    فراخوانی‌ها:
        اعتبارسنجی Pydantic.
    علت:
        ابزار update قبل از SQL باید ورودی نامعتبر را با INVALID_INPUT رد کند.
        پیش‌فرض‌های create اینجا اعمال نمی‌شود تا فیلد نیامده عوض نشود.
    """

    id: int = Field(
        ge=1,
        description="شناسه کاربر در users؛ عدد صحیح مثبت",
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام؛ اگر بیاید نباید خالی باشد",
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام خانوادگی؛ اگر بیاید نباید خالی باشد",
    )
    username: Optional[str] = Field(
        default=None,
        max_length=80,
        description="نام کاربری یکتا؛ اگر بیاید نباید خالی باشد",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=_PASSWORD_MIN_LENGTH,
        max_length=_PASSWORD_MAX_LENGTH,
        description="رمز خام جدید؛ اگر بیاید دوباره هش می‌شود",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="شماره تلفن یکتا",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="ایمیل یکتا",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="فعال بودن حساب",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        """True/False را به‌جای شناسه نمی‌پذیرد."""
        return reject_bool_for_int(value)

    @field_validator("first_name", "last_name", "username", "phone")
    @classmethod
    def _optional_text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        """رشتهٔ داده‌شده را اگر خالی باشد رد می‌کند."""
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("email")
    @classmethod
    def _optional_email_valid(cls, value: Optional[str]) -> Optional[str]:
        """ایمیل داده‌شده را اگر خالی یا بی‌قالب باشد رد می‌کند."""
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        if not _EMAIL_RE.match(value):
            raise ValueError("قالب ایمیل معتبر نیست")
        return value.lower()

    @model_validator(mode="after")
    def _require_writable_field(self):
        """حداقل یک ستون قابل‌نوشتن باید آمده باشد."""
        values = self.model_dump(exclude={"id"})
        if not any(value is not None for value in values.values()):
            raise ValueError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
        return self


class UpdateUserOutput(BaseModel):
    """خروجی موفق به‌روزرسانی کاربر."""

    status: str = Field(default="success", description="همیشه success")
    message: str = Field(description="پیام خوانا برای کلاینت")
    id: int = Field(description="شناسه کاربر به‌روزرسانی‌شده در users")
    model_config = ConfigDict(extra="forbid")


class DeleteUserInput(GetUserInput):
    """ورودی حذف یک کاربر با شناسه."""


class DeleteUserOutput(BaseModel):
    """خروجی موفق حذف کاربر."""

    status: str = Field(default="success", description="همیشه success")
    message: str = Field(description="پیام خوانا برای کلاینت")
    id: int = Field(description="شناسه کاربر حذف‌شده در users")
    model_config = ConfigDict(extra="forbid")
