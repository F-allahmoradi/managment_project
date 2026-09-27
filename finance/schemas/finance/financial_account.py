"""اسکیمای ورودی ابزارهای حساب مالی.

مانده را کلاینت نمی‌نویسد؛ از جمع تراکنش‌ها می‌آید.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.finance.common import PaginationInput, reject_bool_for_int


class CreateFinancialAccountInput(BaseModel):
    """ورودی ساخت حساب. نوع از seed است مثل بودجه پروژه."""

    name: str = Field(min_length=1, max_length=200, description="نام حساب")
    account_type_id: Optional[int] = Field(default=None, ge=1)
    account_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل بودجه پروژه یا صندوق پروژه",
    )
    is_active: bool = Field(default=True, description="حساب فعال باشد")
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("account_type_id", mode="before")
    @classmethod
    def _reject_bool_for_type_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("name", "account_type")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_account_type(self):
        if self.account_type_id is None and not self.account_type:
            raise ValueError("نوع حساب با شناسه یا نام لازم است")
        return self


class GetFinancialAccountInput(BaseModel):
    """ورودی خواندن یک حساب با شناسه."""

    id: int = Field(ge=1, description="شناسه حساب در financial_accounts")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class ListFinancialAccountsInput(PaginationInput):
    """فهرست حساب‌ها؛ فیلتر فعال بودن اختیاری است."""

    is_active: Optional[bool] = Field(
        default=None,
        description="اگر بیاید فقط فعال یا غیرفعال",
    )
