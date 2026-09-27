"""اسکیمای ورودی ابزارهای ممیزی.

ساختن دستی از چت نیست؛ فقط فهرست و خواندن با مجوز AuditLog/Read.
"""

from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class GetAuditLogInput(IdInput):
    """ورودی خواندن یک ردیف ممیزی با شناسه."""


class ListAuditLogsInput(PaginationInput):
    """فهرست ممیزی با فیلتر اختیاری موجودیت و عامل."""

    entity: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=80,
        description="نام موجودیت مثل Task یا ProjectMember",
    )
    entity_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه همان موجودیت",
    )
    user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه کاربری که تغییر را انجام داده",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("entity_id", "user_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("entity")
    @classmethod
    def _entity_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value
