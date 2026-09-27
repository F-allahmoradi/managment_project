"""اسکیمای اتصال مجوز به نقش در role_permissions."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateRolePermissionInput(BaseModel):
    """ورودی دادن یک مجوز به یک نقش."""

    role_id: int = Field(ge=1, description="شناسه نقش")
    permission_id: int = Field(ge=1, description="شناسه مجوز")
    model_config = ConfigDict(extra="forbid")

    @field_validator("role_id", "permission_id", mode="before")
    @classmethod
    def _reject_bool_for_id(cls, value):
        return reject_bool_for_int(value)


class DeleteRolePermissionInput(IdInput):
    """ورودی گرفتن مجوز از نقش با شناسه ردیف اتصال."""


class ListRolePermissionsInput(PaginationInput):
    """فهرست مجوزهای یک نقش؛ role_id اختیاری است."""

    role_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط مجوزهای همین نقش",
    )

    @field_validator("role_id", mode="before")
    @classmethod
    def _reject_bool_for_role_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)
