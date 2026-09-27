"""اسکیمای ورودی ابزارهای MessageRecipient.

هر ردیف دقیقاً یکی از user_id یا external_contact_id را دارد.
هر دو پر یا هر دو خالی رد می‌شود.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import PaginationInput, reject_bool_for_int


class CreateMessageRecipientInput(BaseModel):
    """ورودی افزودن یک گیرنده به یک پیام موجود."""

    message_id: int = Field(ge=1, description="شناسه پیام")
    user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ کاربر سامانه",
    )
    external_contact_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="گیرندهٔ مخاطب خارجی",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator("message_id", "user_id", "external_contact_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @model_validator(mode="after")
    def _require_exactly_one_target(self):
        has_user = self.user_id is not None
        has_external = self.external_contact_id is not None
        if has_user == has_external:
            raise ValueError(
                "گیرنده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
            )
        return self


class ListMessageRecipientsInput(PaginationInput):
    """فهرست گیرنده‌های یک پیام."""

    message_id: int = Field(ge=1, description="شناسه پیام")

    @field_validator("message_id", mode="before")
    @classmethod
    def _reject_bool_for_message_id(cls, value):
        return reject_bool_for_int(value)
