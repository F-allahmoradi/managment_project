"""اسکیمای ورودی ابزارهای تراکنش مالی.

مبلغ صفر رد می‌شود. project_id و user_id اختیاری‌اند.
حذف نرم در این اسکیما نیست؛ جبران با بازگشت وجه است.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.finance.common import PaginationInput, reject_bool_for_int


class CreateFinancialTransactionInput(BaseModel):
    """ورودی ثبت دریافت یا پرداخت روی یک حساب."""

    account_id: int = Field(ge=1, description="شناسه حساب")
    amount: Decimal = Field(description="مبلغ؛ صفر رد می‌شود")
    transaction_type_id: Optional[int] = Field(default=None, ge=1)
    transaction_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل دریافت یا پرداخت",
    )
    project_id: Optional[int] = Field(default=None, ge=1)
    user_id: Optional[int] = Field(default=None, ge=1)
    category_id: Optional[int] = Field(default=None, ge=1)
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام دسته seed مثل تجهیزات یا حقوق",
    )
    description: Optional[str] = Field(default=None)
    transaction_date: Optional[date] = Field(
        default=None,
        description="تاریخ تراکنش؛ پیش‌فرض امروز",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "account_id",
        "transaction_type_id",
        "project_id",
        "user_id",
        "category_id",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("amount", mode="before")
    @classmethod
    def _parse_amount(cls, value):
        if isinstance(value, bool):
            raise ValueError("مبلغ باید عدد باشد نه بولین")
        return value

    @field_validator("amount")
    @classmethod
    def _amount_not_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("مبلغ صفر مجاز نیست")
        return value

    @field_validator("transaction_date", mode="before")
    @classmethod
    def _parse_date(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value)[:10])

    @field_validator("transaction_type", "category", "description")
    @classmethod
    def _optional_text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_transaction_type(self):
        if self.transaction_type_id is None and not self.transaction_type:
            raise ValueError("نوع تراکنش با شناسه یا نام لازم است")
        return self


class ListFinancialTransactionsInput(PaginationInput):
    """فهرست تراکنش‌ها با فیلتر اختیاری حساب یا پروژه."""

    account_id: Optional[int] = Field(default=None, ge=1)
    project_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("account_id", "project_id", mode="before")
    @classmethod
    def _reject_bool_for_filter_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
