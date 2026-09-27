"""اسکیمای ورودی ابزارهای Issue.

عنوان و پروژه و وضعیت seed اینجا است. منبع تحلیل از طریق
issue_sources وصل می‌شود. زنجیرهٔ علت با link_issue_cause است.
وظیفه با create_task ساخته می‌شود و با link_issue_task وصل می‌گردد.
اهمیت، فوریت، شدت و اثر بعد از وصل وظیفه با ابزار جدا است.
موضوع و موجودیت ذخیره‌شدهٔ NER با link_issue_topic و
link_issue_entity به مسئلهٔ canonical وصل می‌شوند.
created_by_user_id از کاربر جاری می‌آید.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int


class CreateIssueInput(BaseModel):
    """ورودی ثبت یک مسئله در issues و وصل تحلیل در issue_sources."""

    project_id: int = Field(ge=1, description="شناسه پروژه؛ الزامی")
    title: str = Field(
        min_length=1,
        max_length=200,
        description="عنوان کوتاه مسئله؛ الزامی و غیرخالی",
    )
    analysis_id: int = Field(
        ge=1,
        description="شناسه text_analyses که این مسئله را از متن درآورده",
    )
    status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه وضعیت در issue_statuses",
    )
    status: Optional[str] = Field(
        default="جدید",
        max_length=100,
        description="نام یا کد وضعیت seed مثل جدید یا new",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("project_id", "analysis_id", "status_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("title", "status")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value


class GetIssueInput(IdInput):
    """ورودی خواندن یک مسئله با شناسه."""


class ListIssuesInput(PaginationInput):
    """فهرست مسائل پروژه‌هایی که کاربر عضو فعال‌شان است."""

    project_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="اگر بیاید فقط مسائل همین پروژه",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def _reject_bool_for_project_id(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)


class LinkIssueCauseInput(BaseModel):
    """ورودی وصل دو مسئله در issue_causes با سطح علت یا ریشه."""

    issue_id: int = Field(ge=1, description="شناسه مسئلهٔ معلول")
    cause_issue_id: int = Field(ge=1, description="شناسه مسئلهٔ علت")
    cause_level_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه سطح در cause_levels",
    )
    cause_level: Optional[str] = Field(
        default="علت",
        max_length=100,
        description="نام یا کد seed مثل علت / cause یا ریشه / root_cause",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "cause_issue_id", "cause_level_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("cause_level")
    @classmethod
    def _level_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _not_self(self):
        if self.issue_id == self.cause_issue_id:
            raise ValueError("مسئله نمی‌تواند علت خودش باشد")
        return self


class LinkIssueTaskInput(BaseModel):
    """ورودی وصل مسئله به وظیفهٔ موجود در issue_tasks."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    task_id: int = Field(ge=1, description="شناسه وظیفه در tasks")
    model_config = ConfigDict(extra="forbid")

    @field_validator("issue_id", "task_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        return reject_bool_for_int(value)


class SetIssueImportanceInput(BaseModel):
    """ورودی تنظیم اهمیت مسئله از کاتالوگ task_importances."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    importance_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه اهمیت در task_importances",
    )
    importance: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام seed مثل زیاد یا حیاتی",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "importance_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("importance")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.importance_id is None and not self.importance:
            raise ValueError("اهمیت با شناسه یا نام لازم است")
        return self


class SetIssueUrgencyInput(BaseModel):
    """ورودی تنظیم فوریت مسئله از کاتالوگ task_priorities."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    priority_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه فوریت در task_priorities",
    )
    priority: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام seed مثل کم یا فوری؛ معمولاً همان اولویت وظیفه",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "priority_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("priority")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.priority_id is None and not self.priority:
            raise ValueError("فوریت با شناسه یا نام لازم است")
        return self


class SetIssueSeverityInput(BaseModel):
    """ورودی تنظیم شدت مسئله از کاتالوگ severity_levels."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    severity_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه شدت در severity_levels",
    )
    severity: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام یا کد seed مثل متوسط / medium",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "severity_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("severity")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.severity_id is None and not self.severity:
            raise ValueError("شدت با شناسه یا نام لازم است")
        return self


class AddIssueImpactInput(BaseModel):
    """ورودی افزودن یک اثر مسئله از کاتالوگ impact_types."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    impact_type_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نوع اثر در impact_types",
    )
    impact_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="نام یا کد seed مثل کیفیت / quality یا منابع انسانی / hr",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=300,
        description="شرح اثر؛ اگر خالی باشد نام نوع seed نوشته می‌شود",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "impact_type_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("impact_type", "description")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.impact_type_id is None and not self.impact_type:
            raise ValueError("نوع اثر با شناسه یا نام لازم است")
        return self


class LinkIssueTopicInput(BaseModel):
    """ورودی وصل موضوع ذخیره‌شدهٔ NER به مسئله در issue_topics."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    topic_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه موضوع در topics",
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=80,
        description="کد یا نام seed مثل finance.payment.delay یا تأخیر پرداخت",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "topic_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("topic")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.topic_id is None and not self.topic:
            raise ValueError("موضوع با شناسه یا کد لازم است")
        return self


class LinkIssueEntityInput(BaseModel):
    """ورودی وصل موجودیت ذخیره‌شدهٔ NER به مسئله با نقش seed."""

    issue_id: int = Field(ge=1, description="شناسه مسئله")
    entity_id: int = Field(ge=1, description="شناسه موجودیت در entities")
    role_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="شناسه نقش در issue_entity_roles",
    )
    role: Optional[str] = Field(
        default="ذکرشده",
        max_length=100,
        description="نام یا کد seed مثل متأثر / affected یا مسئول / responsible",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("issue_id", "entity_id", "role_id", mode="before")
    @classmethod
    def _reject_bool_for_ids(cls, value):
        if value is None:
            return None
        return reject_bool_for_int(value)

    @field_validator("role")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _need_lookup(self):
        if self.role_id is None and not self.role:
            raise ValueError("نقش با شناسه یا نام لازم است")
        return self
