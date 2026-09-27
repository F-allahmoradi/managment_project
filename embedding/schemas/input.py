"""مدل اعتبارسنجی ورودی ایندکس و جستجوی معنایی."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMBED_KINDS = frozenset({"raw", "entity", "intent", "intent_slot"})
_SOURCE_TYPES = frozenset({"meeting", "message", "content"})


class IndexTextAnalysisInput(BaseModel):
    """ورودی برداری‌کردن یک تحلیل ذخیره‌شده."""

    analysis_id: int = Field(ge=1, description="شناسه text_analyses")
    model_config = ConfigDict(extra="forbid")

    @field_validator("analysis_id", mode="before")
    @classmethod
    def _reject_bool_for_int(cls, value):
        if isinstance(value, bool):
            raise ValueError("باید عدد صحیح باشد نه بولین")
        return value


class IndexPendingInput(BaseModel):
    """ورودی ایندکس تحلیل‌هایی که هنوز بردار ندارند."""

    limit: int = Field(default=20, ge=1, le=50)
    model_config = ConfigDict(extra="forbid")

    @field_validator("limit", mode="before")
    @classmethod
    def _reject_bool_for_int(cls, value):
        if isinstance(value, bool):
            raise ValueError("باید عدد صحیح باشد نه بولین")
        return value


class SearchSimilarInput(BaseModel):
    """ورودی جستجوی موارد مشابه از روی بردار."""

    query: str = Field(min_length=1, max_length=2000, description="سؤال به زبان طبیعی")
    kinds: Optional[list[str]] = Field(
        default=None,
        description="خام، موجودیت، نیت یا جزء نیت؛ خالی یعنی همه",
    )
    source_type: Optional[str] = Field(default=None, max_length=40)
    limit: int = Field(default=8, ge=1, le=20)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("limit", mode="before")
    @classmethod
    def _reject_bool_limit(cls, value):
        if isinstance(value, bool):
            raise ValueError("باید عدد صحیح باشد نه بولین")
        return value

    @field_validator("query")
    @classmethod
    def _query_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("سؤال خالی است")
        return value

    @field_validator("source_type")
    @classmethod
    def _optional_source(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        code = value.strip().lower()
        if code not in _SOURCE_TYPES:
            raise ValueError("source_type باید meeting یا message یا content باشد")
        return code

    @field_validator("kinds")
    @classmethod
    def _known_kinds(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned = []
        seen = set()
        for item in value:
            kind = str(item or "").strip().lower()
            if kind not in _EMBED_KINDS:
                raise ValueError("kind باید raw یا entity یا intent یا intent_slot باشد")
            if kind not in seen:
                cleaned.append(kind)
                seen.add(kind)
        return cleaned or None
