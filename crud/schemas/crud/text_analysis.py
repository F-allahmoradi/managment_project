"""اسکیمای ورودی ذخیره و خواندن تحلیل متن.

خروجی NER همین شکل را دارد. INSERT در NER نیست؛ اینجا نوشته می‌شود.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.crud.common import IdInput, PaginationInput, reject_bool_for_int

_SOURCE_TYPES = frozenset({"meeting", "message", "content"})
_ENTITY_TYPES = frozenset(
    {"PERSON", "UNIT", "ORG", "PLACE", "OBJECT", "PROJECT", "TASK", "TIME", "ROLE"}
)


def _reject_bool_ids(value):
    if value is None:
        return None
    return reject_bool_for_int(value)


def _optional_mention_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


class SaveMentionInput(BaseModel):
    """یک ذکر آمادهٔ entity_mentions."""

    type: str = Field(min_length=1, max_length=40, description="کد نوع مثل PERSON")
    canonical_name: str = Field(min_length=1, max_length=200)
    normalized_name: Optional[str] = Field(default=None, max_length=200)
    mention_text: str = Field(min_length=1, max_length=300)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=1)
    confidence: float = Field(default=1, ge=0, le=1)
    occurred_at: Optional[datetime] = Field(default=None)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("start_offset", "end_offset", mode="before")
    @classmethod
    def _reject_bool_offsets(cls, value):
        return reject_bool_for_int(value)

    @field_validator("type")
    @classmethod
    def _known_type(cls, value: str) -> str:
        code = value.strip().upper()
        if code not in _ENTITY_TYPES:
            raise ValueError("نوع موجودیت نامعتبر است")
        return code

    @field_validator("canonical_name", "normalized_name", "mention_text")
    @classmethod
    def _text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @model_validator(mode="after")
    def _offsets_and_name(self):
        if self.end_offset <= self.start_offset:
            raise ValueError("اندیس پایان باید بعد از شروع باشد")
        if not self.normalized_name:
            self.normalized_name = self.canonical_name
        return self


class SaveKeywordInput(BaseModel):
    """یک عبارت کلیدی آمادهٔ keyword_mentions."""

    phrase: str = Field(min_length=1, max_length=200)
    mention_text: str = Field(default="", max_length=300)
    start_offset: int = Field(default=-1)
    end_offset: int = Field(default=-1)
    confidence: float = Field(default=1, ge=0, le=1)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("phrase")
    @classmethod
    def _phrase_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("عبارت کلیدی خالی است")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("start_offset", "end_offset", mode="before")
    @classmethod
    def _reject_bool_offsets(cls, value):
        return reject_bool_for_int(value)


class SaveTopicInput(BaseModel):
    """یک موضوع آمادهٔ text_analysis_topics."""

    code: str = Field(min_length=1, max_length=80)
    is_primary: bool = False
    confidence: float = Field(default=1, ge=0, le=1)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    discovered: bool = False
    name: Optional[str] = Field(default=None, max_length=100)
    definition: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("code")
    @classmethod
    def _code_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("کد موضوع خالی است")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)


class SaveSentimentInput(BaseModel):
    """قطبیت کل متن."""

    polarity: str = Field(min_length=1, max_length=40)
    intensity: str = Field(min_length=1, max_length=40)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)


class SaveEmotionInput(BaseModel):
    """یک هیجان آمادهٔ text_analysis_emotions."""

    emotion: str = Field(min_length=1, max_length=40)
    intensity: str = Field(min_length=1, max_length=40)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)


class SaveDiscourseInput(BaseModel):
    """یک ژانر آمادهٔ text_analysis_discourses."""

    code: str = Field(min_length=1, max_length=40)
    is_primary: bool = False
    confidence: float = Field(default=1, ge=0, le=1)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    discovered: bool = False
    name: Optional[str] = Field(default=None, max_length=100)
    definition: Optional[str] = Field(default=None)
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="نقش‌های پرشدهٔ ژانر",
    )
    required_slots: list = Field(default_factory=list)
    optional_slots: list = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("code")
    @classmethod
    def _code_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("کد ژانر خالی است")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("slots", mode="before")
    @classmethod
    def _clean_slots(cls, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("اجزای ژانر باید شیء باشد")
        cleaned = {}
        for key, item in value.items():
            name = str(key or "").strip()
            text = str(item or "").strip()
            if not name or not text:
                continue
            cleaned[name[:100]] = text[:300]
        return cleaned

    @model_validator(mode="before")
    @classmethod
    def _flatten_schema(cls, data):
        if not isinstance(data, dict):
            return data
        schema = data.get("type_schema")
        if not isinstance(schema, dict):
            return data
        merged = dict(data)
        if not merged.get("name"):
            merged["name"] = schema.get("name")
        if not merged.get("definition"):
            merged["definition"] = schema.get("definition")
        if not merged.get("required_slots"):
            merged["required_slots"] = schema.get("required_slots") or []
        if not merged.get("optional_slots"):
            merged["optional_slots"] = schema.get("optional_slots") or []
        if schema.get("code") and not merged.get("discovered"):
            merged["discovered"] = True
        return merged


class SaveIntentInput(BaseModel):
    """یک نیت آمادهٔ text_analysis_intents."""

    code: str = Field(min_length=1, max_length=40)
    is_primary: bool = False
    confidence: float = Field(default=1, ge=0, le=1)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="اجزای پرشدهٔ نیت مثل شاکی و خواسته",
    )
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("code")
    @classmethod
    def _code_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("کد نیت خالی است")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("slots", mode="before")
    @classmethod
    def _clean_slots(cls, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("اجزای نیت باید شیء باشد")
        cleaned = {}
        for key, item in value.items():
            name = str(key or "").strip()
            text = str(item or "").strip()
            if not name or not text:
                continue
            cleaned[name[:100]] = text[:300]
        return cleaned


class SaveRhetoricInput(BaseModel):
    """یک صنعت بیان آمادهٔ text_analysis_rhetorics."""

    code: str = Field(min_length=1, max_length=40)
    is_primary: bool = False
    confidence: float = Field(default=1, ge=0, le=1)
    mention_text: str = Field(default="", max_length=300, description="شاهد کوتاه از متن")
    intended_meaning: str = Field(
        default="",
        description="بازنویسیٔ صریح غرض گوینده",
    )
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="نقش‌های پرشده مثل ظاهر و مقصود",
    )
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("code")
    @classmethod
    def _code_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("کد صنعت بیان خالی است")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("intended_meaning", mode="before")
    @classmethod
    def _optional_meaning(cls, value):
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("slots", mode="before")
    @classmethod
    def _clean_slots(cls, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("اجزای بیان باید شیء باشد")
        cleaned = {}
        for key, item in value.items():
            name = str(key or "").strip()
            text = str(item or "").strip()
            if not name or not text:
                continue
            cleaned[name[:100]] = text[:300]
        return cleaned


def _string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        raise ValueError("باید فهرست باشد")
    items = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text[:300])
    return items


class SaveFactInput(BaseModel):
    """یک فکت آمادهٔ text_analysis_facts."""

    kind: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    value: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=40)
    role: str = Field(default="none", min_length=1, max_length=40)
    grounding: str = Field(min_length=1, max_length=40)
    derivation: str = Field(default="", max_length=40)
    effect: str = Field(default="", max_length=300)
    previous: str = Field(default="", max_length=300)
    current: str = Field(default="", max_length=300)
    fact_id: str = Field(default="", max_length=40)
    mention_text: str = Field(default="", max_length=300)
    start_offset: int = Field(default=-1)
    end_offset: int = Field(default=-1)
    evidence_texts: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1, ge=0, le=1)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, data):
        if not isinstance(data, dict):
            return data
        merged = dict(data)
        if not merged.get("kind"):
            merged["kind"] = merged.get("type")
        if not merged.get("name"):
            merged["name"] = merged.get("label")
        if not merged.get("mention_text"):
            merged["mention_text"] = merged.get("evidence")
        if not merged.get("fact_id"):
            merged["fact_id"] = merged.get("id") or merged.get("fact_code")
        return merged

    @field_validator("kind", "grounding", "role")
    @classmethod
    def _code_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("کد فکت خالی است")
        return value

    @field_validator("unit", mode="before")
    @classmethod
    def _optional_unit(cls, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("derivation", "effect", "previous", "current", "fact_id", mode="before")
    @classmethod
    def _optional_text(cls, value):
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("start_offset", "end_offset", mode="before")
    @classmethod
    def _reject_bool_offsets(cls, value):
        return reject_bool_for_int(value)

    @field_validator("evidence_texts", "source_ids", mode="before")
    @classmethod
    def _list_texts(cls, value):
        return _string_list(value)

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نام فکت خالی است")
        return value


class SaveQuoteInput(BaseModel):
    """یک نقل‌قول آمادهٔ text_analysis_quotes."""

    mode: str = Field(min_length=1, max_length=40)
    attributed_to: str = Field(min_length=1, max_length=200)
    quoted_text: str = Field(min_length=1)
    mention_text: str = Field(default="", max_length=300)
    start_offset: int = Field(default=-1)
    end_offset: int = Field(default=-1)
    confidence: float = Field(default=1, ge=0, le=1)
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, data):
        if not isinstance(data, dict):
            return data
        merged = dict(data)
        if not merged.get("mode"):
            merged["mode"] = merged.get("type")
        if not merged.get("attributed_to"):
            merged["attributed_to"] = merged.get("speaker")
        if not merged.get("quoted_text"):
            merged["quoted_text"] = merged.get("content")
        if not merged.get("mention_text"):
            merged["mention_text"] = merged.get("evidence") or merged.get("cue")
        return merged

    @field_validator("mode", "attributed_to", "quoted_text")
    @classmethod
    def _text_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نمی‌تواند خالی باشد")
        return value

    @field_validator("mention_text", mode="before")
    @classmethod
    def _optional_mention(cls, value):
        return _optional_mention_text(value)

    @field_validator("start_offset", "end_offset", mode="before")
    @classmethod
    def _reject_bool_offsets(cls, value):
        return reject_bool_for_int(value)


class SaveTextAnalysisInput(BaseModel):
    """ورودی ذخیره یک اجرای تحلیل روی منبع عملیاتی."""

    source_type: str = Field(min_length=1, max_length=40)
    source_id: Optional[int] = Field(default=None, ge=1)
    text: Optional[str] = Field(default=None, description="فقط برای پیش‌نویس content")
    model: str = Field(default="deepseek-v4-flash", min_length=1, max_length=120)
    mentions: list[SaveMentionInput] = Field(default_factory=list)
    keywords: list[SaveKeywordInput] = Field(default_factory=list)
    topics: list[SaveTopicInput] = Field(default_factory=list)
    sentiment: Optional[SaveSentimentInput] = None
    emotions: list[SaveEmotionInput] = Field(default_factory=list)
    discourses: list[SaveDiscourseInput] = Field(default_factory=list)
    intents: list[SaveIntentInput] = Field(default_factory=list)
    rhetorics: list[SaveRhetoricInput] = Field(default_factory=list)
    facts: list[SaveFactInput] = Field(default_factory=list)
    quotes: list[SaveQuoteInput] = Field(default_factory=list)
    intended_meaning: Optional[str] = Field(
        default=None,
        description="بازنویسیٔ صریح سطح سند؛ اگر خالی باشد از بیان اصلی می‌آید",
    )
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("source_id", mode="before")
    @classmethod
    def _reject_bool_source_id(cls, value):
        return _reject_bool_ids(value)

    @field_validator("source_type")
    @classmethod
    def _known_source(cls, value: str) -> str:
        code = value.strip().lower()
        if code not in _SOURCE_TYPES:
            raise ValueError("source_type باید meeting یا message یا content باشد")
        return code

    @field_validator("model")
    @classmethod
    def _model_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("نام مدل خالی است")
        return value

    @field_validator("text")
    @classmethod
    def _optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def _require_source(self):
        if self.source_type == "content":
            if self.source_id is None and not self.text:
                raise ValueError("برای content یا source_id لازم است یا text")
            return self
        if self.source_id is None:
            raise ValueError("source_id برای این نوع منبع لازم است")
        return self


class GetTextAnalysisInput(IdInput):
    """ورودی خواندن یک تحلیل با شناسه."""


class ListTextAnalysesInput(PaginationInput):
    """فهرست تحلیل‌هایی که کاربر جاری ساخته است."""

    source_type: Optional[str] = Field(default=None, max_length=40)
    source_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("source_id", mode="before")
    @classmethod
    def _reject_bool_source_id(cls, value):
        return _reject_bool_ids(value)

    @field_validator("source_type")
    @classmethod
    def _optional_source(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        code = value.strip().lower()
        if code not in _SOURCE_TYPES:
            raise ValueError("source_type نامعتبر است")
        return code
