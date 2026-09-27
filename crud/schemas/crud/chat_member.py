"""اسکیمای ورودی ابزارهای ChatMember.

عضو گفتگو فقط کاربر سامانه است؛ مخاطب خارجی اینجا اضافه نمی‌شود.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.crud.common import PaginationInput, reject_bool_for_int


class CreateChatMemberInput(BaseModel):
    """ورودی افزودن یک کاربر سامانه به یک گفتگو."""

    chat_id: int = Field(ge=1, description="شناسه گفتگو")
    user_id: int = Field(ge=1, description="شناسه کاربر سامانه")
    model_config = ConfigDict(extra="forbid")

    @field_validator("chat_id", "user_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        return reject_bool_for_int(value)


class ListChatMembersInput(PaginationInput):
    """فهرست اعضای یک گفتگو."""

    chat_id: int = Field(ge=1, description="شناسه گفتگو")

    @field_validator("chat_id", mode="before")
    @classmethod
    def _reject_bool_for_chat_id(cls, value):
        return reject_bool_for_int(value)
