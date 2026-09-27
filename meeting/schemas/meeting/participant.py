"""اسکیمای ورودی شرکت‌کنندهٔ جلسه.

هر ردیف دقیقاً یکی از user_id یا external_contact_id را دارد.
هر دو پر یا هر دو خالی رد می‌شود.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.meeting.common import reject_bool_for_int


class CreateMeetingParticipantInput(BaseModel):
    """ورودی افزودن یک شرکت‌کننده به یک جلسه موجود."""

    meeting_id: int = Field(ge=1, description="شناسه جلسه")
    user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شرکت‌کنندهٔ کاربر سامانه",
    )
    external_contact_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شرکت‌کنندهٔ مخاطب خارجی",
    )
    role: Optional[str] = Field(default=None, max_length=50)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("meeting_id", "user_id", "external_contact_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("role")
    @classmethod
    def _role_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_exactly_one_target(self):
        has_user = self.user_id is not None
        has_external = self.external_contact_id is not None
        if has_user == has_external:
            raise ValueError(
                "شرکت‌کننده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
            )
        return self
