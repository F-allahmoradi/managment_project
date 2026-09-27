"""اسکیمای ورودی مشترک شناسه و صفحه‌بندی فهرست‌های CRUD."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


def reject_bool_for_int(value):
    """True/False را به‌جای عدد صحیح نمی‌پذیرد."""
    if isinstance(value, bool):
        raise ValueError("باید عدد صحیح باشد نه بولین")
    return value


class IdInput(BaseModel):
    """شناسه مثبت یک ردیف؛ بولین را به‌جای عدد رد می‌کند."""

    id: int = Field(
        ge=1,
        description="شناسه ردیف؛ عدد صحیح مثبت",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        """True/False را به‌جای شناسه نمی‌پذیرد."""
        return reject_bool_for_int(value)


class PaginationInput(BaseModel):
    """صفحه‌بندی مشترک فهرست‌ها؛ سقف ۵۰ با policies.yaml یکی است."""

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="تعداد رکورد در هر صفحه؛ پیش‌فرض ۱۰، حداکثر ۵۰",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="تعداد رکورد ردشده از ابتدا؛ پیش‌فرض ۰",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("limit", "offset", mode="before")
    @classmethod
    def _reject_bool_for_page(cls, value):
        """True/False را به‌جای عدد صفحه‌بندی نمی‌پذیرد."""
        return reject_bool_for_int(value)
