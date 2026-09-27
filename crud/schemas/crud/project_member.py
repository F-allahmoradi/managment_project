"""اسکیمای ورودی ابزارهای ProjectMember.

نقش اینجا نقش داخل پروژه است (project_roles)، نه نقش سراسری roles.
افزودن عضو، تغییر نقش داخل پروژه، و فعال/غیرفعال.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import PaginationInput, reject_bool_for_int


class CreateProjectMemberInput(BaseModel):
    """ورودی افزودن یک عضو به یک پروژه."""

    project_id: int = Field(ge=1, description="شناسه پروژه")
    user_id: int = Field(ge=1, description="شناسه کاربری که عضو می‌شود")
    project_role_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نقش داخل پروژه در project_roles",
    )
    project_role: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نقش داخل پروژه مثل عضو یا ناظر",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("project_id", "user_id", "project_role_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("project_role")
    @classmethod
    def _role_name_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_project_role(self):
        if self.project_role_id is None and not self.project_role:
            raise ValueError("نقش داخل پروژه با شناسه یا نام لازم است")
        return self


class ListProjectMembersInput(PaginationInput):
    """فهرست اعضای یک پروژه."""

    project_id: int = Field(ge=1, description="شناسه پروژه")

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        return reject_bool_for_int(value)


class UpdateProjectMemberInput(BaseModel):
    """ورودی تغییر نقش داخل پروژه یا فعال/غیرفعال بودن عضویت."""

    id: int = Field(ge=1, description="شناسه ردیف project_members")
    project_role_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نقش داخل پروژه",
    )
    project_role: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام نقش داخل پروژه مثل عضو",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="فعال بودن عضویت در همین پروژه",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("id", "project_role_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("project_role")
    @classmethod
    def _role_name_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _require_writable_field(self):
        if (
            self.project_role_id is None
            and self.project_role is None
            and self.is_active is None
        ):
            raise ValueError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
        return self
