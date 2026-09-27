"""اسکیمای ورودی ابزارهای PerformanceAction.

تشویق و تنبیه رویداد جدا است؛ روی User فیلد امتیاز یا مبلغ نیست.
نوع از seed است (تقدیر، پاداش نقدی، اخطار، جریمه، …).
اگر مبلغ باشد حساب لازم است تا همان لحظه تراکنش ساخته شود.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreatePerformanceActionInput(BaseModel):
    """ورودی ثبت یک تشویق یا تنبیه روی کاربر."""

    user_id: int = Field(ge=1, description="کاربری که ارزیابی می‌شود")
    reason: str = Field(min_length=1, description="دلیل اقدام؛ الزامی")
    action_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع در performance_action_types",
    )
    action_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نوع seed مثل تقدیر یا پاداش نقدی",
    )
    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="پروژهٔ اختیاری همان اقدام",
    )
    score: Optional[int] = Field(
        default=None,
        description="امتیاز؛ صفر رد می‌شود. بدون مبلغ مجاز است",
    )
    amount: Optional[Decimal] = Field(
        default=None,
        description="مبلغ نقدی؛ صفر رد می‌شود. بدون حساب رد می‌شود",
    )
    account_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="حساب تراکنش؛ فقط وقتی amount باشد",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator(
        "user_id",
        "action_type_id",
        "project_id",
        "account_id",
        "score",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("reason", "action_type")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("score")
    @classmethod
    def _score_not_zero(cls, value: Optional[int]) -> Optional[int]:
        if value == 0:
            raise ValueError("امتیاز صفر مجاز نیست")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def _parse_amount(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("مبلغ باید عدد باشد نه بولین")
        return value

    @field_validator("amount")
    @classmethod
    def _amount_not_zero(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value == 0:
            raise ValueError("مبلغ صفر مجاز نیست")
        return value

    @model_validator(mode="after")
    def _require_type_and_cash_account(self):
        if self.action_type_id is None and not self.action_type:
            raise ValueError("نوع اقدام با شناسه یا نام لازم است")
        if self.amount is not None and self.account_id is None:
            raise ValueError("برای مبلغ نقدی حساب لازم است")
        if self.account_id is not None and self.amount is None:
            raise ValueError("حساب بدون مبلغ نقدی مجاز نیست")
        return self


class GetPerformanceActionInput(IdInput):
    """ورودی خواندن یک اقدام با شناسه."""


class ListPerformanceActionsInput(PaginationInput):
    """فهرست اقدامات با فیلتر اختیاری کاربر یا پروژه."""

    user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط اقدامات همین کاربر",
    )
    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط اقدامات همین پروژه",
    )

    @field_validator("user_id", "project_id", mode="before")
    @classmethod
    def _reject_bool_for_filter_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
