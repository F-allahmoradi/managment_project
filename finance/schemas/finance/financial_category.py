"""اسکیمای ورودی افزودن دستهٔ مالی.

نوع تراکنش ابزار کامل ندارد؛ دسته را می‌شود در همین گام افزود.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.finance.common import reject_bool_for_int


class CreateFinancialCategoryInput(BaseModel):
    """ورودی افزودن دستهٔ هزینه یا درآمد."""

    name: str = Field(min_length=1, max_length=100, description="نام دسته")
    description: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name", "description")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value


class GetFinancialCategoryInput(BaseModel):
    """ورودی خواندن یک دسته با شناسه؛ ابزار MCP این گام ثبت نمی‌شود."""

    id: int = Field(ge=1, description="شناسه دسته در financial_categories")
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)
