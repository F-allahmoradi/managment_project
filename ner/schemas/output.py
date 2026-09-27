"""مدل‌های خروجی استخراج متن پروژه.

لایه span: entities / entity_mentions / keywords
لایه topic: text_analysis_topics
لایه stance: text_analysis_sentiments / text_analysis_emotions
لایه discourse: text_analysis_discourses
لایه intent: text_analysis_intents
لایه rhetoric: text_analysis_rhetorics
INSERT نیست.
"""

from typing import Optional

from pydantic import BaseModel, Field


class EntityMentionHit(BaseModel):
    """یک ذکر در متن؛ ستون‌های entity_mentions به‌علاوه نوع."""

    type: str = Field(description="کد entity_types مثل PERSON یا UNIT")
    canonical_name: str = Field(description="نام canonical برای جدول entities")
    normalized_name: str = Field(description="نام یکدست‌شده برای تطبیق")
    mention_text: str = Field(description="تکهٔ دقیق متن؛ ستون mention_text")
    start_offset: int = Field(description="اندیس شروع در متن نرمال‌شده")
    end_offset: int = Field(description="اندیس پایان در متن نرمال‌شده")
    confidence: float = Field(description="اطمینان استخراج بین ۰ و ۱")
    occurred_at: Optional[str] = Field(
        default=None,
        description="فقط TIME؛ تاریخ/ساعت تبدیل‌شده برای entity_mention_times",
    )


class TopicHit(BaseModel):
    """موضوع از درخت topics؛ آمادهٔ text_analysis_topics."""

    code: str = Field(description="کد موضوع مثل finance.payment.delay")
    name: str = Field(description="نام فارسی موضوع")
    level: int = Field(description="عمق در درخت حوزه")
    parent_code: Optional[str] = Field(
        default=None,
        description="کد والد؛ برای ریشه خالی است",
    )
    path: list[str] = Field(
        default_factory=list,
        description="نام‌های مسیر از ریشه تا همین برگ",
    )
    path_codes: list[str] = Field(
        default_factory=list,
        description="کدهای مسیر از ریشه تا همین برگ",
    )
    is_primary: bool = Field(description="موضوع اصلی همین متن")
    mention_text: str = Field(description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")
    discovered: bool = Field(
        default=False,
        description="اگر گره کاتالوگ نبود و موضوع از متن ساخته شد",
    )
    definition: Optional[str] = Field(
        default=None,
        description="تعریف موضوع کشف‌شده؛ برای گره کاتالوگ خالی است",
    )


class KeywordHit(BaseModel):
    """کلمه یا عبارت کلیدی آزاد از متن؛ موجودیت نام‌دار نیست."""

    phrase: str = Field(description="عبارت کلیدی نرمال‌شده")
    mention_text: str = Field(description="تکهٔ دقیق متن")
    start_offset: int = Field(description="اندیس شروع در متن نرمال‌شده")
    end_offset: int = Field(description="اندیس پایان در متن نرمال‌شده")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class CanonicalEntityHit(BaseModel):
    """موجودیت یکتا پس از ادغام ذکرهای هم‌نام؛ جدول entities."""

    type: str = Field(description="کد نوع موجودیت")
    canonical_name: str = Field(description="نام canonical")
    normalized_name: str = Field(description="نام یکدست‌شده")
    mention_count: int = Field(description="تعداد ذکر در همین متن")


class SentimentHit(BaseModel):
    """قطبیت کل متن؛ آمادهٔ text_analysis_sentiments."""

    polarity: str = Field(description="کد polarities: positive یا negative یا neutral")
    polarity_name: str = Field(description="نام فارسی قطبیت")
    intensity: str = Field(description="کد intensity_levels: low یا medium یا high")
    intensity_name: str = Field(description="نام فارسی شدت")
    intensity_level: int = Field(description="عدد شدت از ۱")
    mention_text: str = Field(default="", description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class EmotionHit(BaseModel):
    """هیجان جدا از قطبیت؛ آمادهٔ text_analysis_emotions."""

    emotion: str = Field(description="کد emotions مثل worry")
    name: str = Field(description="نام فارسی هیجان")
    intensity: str = Field(description="کد شدت")
    intensity_name: str = Field(description="نام فارسی شدت")
    intensity_level: int = Field(description="عدد شدت از ۱")
    mention_text: str = Field(default="", description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class ExtractEntitiesOutput(BaseModel):
    """نتیجه استخراج از متن پروژه. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    table: str = Field(description="جدول هدف ذکرها؛ entity_mentions")
    column: str = Field(description="ستون شاهد؛ mention_text")
    source_type: Optional[str] = Field(
        default=None,
        description="meeting یا message اگر از دیتابیس خوانده شده",
    )
    source_id: Optional[int] = Field(
        default=None,
        description="شناسه منبع اگر از دیتابیس خوانده شده",
    )
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    extracted_count: int = Field(description="تعداد ذکر معتبر")
    canonical_count: int = Field(description="تعداد موجودیت یکتا")
    type_counts: dict[str, int] = Field(
        default_factory=dict,
        description="تعداد ذکر به تفکیک نوع",
    )
    entities: list[CanonicalEntityHit] = Field(
        default_factory=list,
        description="موجودیت‌های canonical آمادهٔ entities",
    )
    mentions: list[EntityMentionHit] = Field(
        default_factory=list,
        description="ذکرها آمادهٔ entity_mentions",
    )


class ExtractKeywordsOutput(BaseModel):
    """نتیجه استخراج کلمهٔ کلیدی. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    keywords: list[KeywordHit] = Field(default_factory=list)
    keyword_count: int = Field(default=0)


class ExtractTopicsOutput(BaseModel):
    """نتیجه طبقه‌بندی موضوع. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    topics: list[TopicHit] = Field(default_factory=list)
    topic_count: int = Field(default=0)


class DiscourseTypeSchema(BaseModel):
    """ساختار یک ژانر نو که از متن کشف شده است."""

    code: str = Field(description="کد انگلیسی نوع کشف‌شده")
    name: str = Field(description="نام فارسی نوع")
    definition: str = Field(description="تعریف نوع از روی شواهد متن")
    required_slots: list[dict[str, str]] = Field(
        default_factory=list,
        description="نقش‌های اجباری همین نوع",
    )
    optional_slots: list[dict[str, str]] = Field(
        default_factory=list,
        description="نقش‌های اختیاری همین نوع",
    )
    contrast: list[str] = Field(
        default_factory=list,
        description="مرز با قالب‌های نزدیک",
    )


class DiscourseHit(BaseModel):
    """ژانر / نوع پیام؛ آمادهٔ text_analysis_discourses."""

    code: str = Field(description="کد discourse_types مثل issue یا request")
    name: str = Field(description="نام فارسی ژانر")
    is_primary: bool = Field(description="ژانر اصلی همین متن")
    mention_text: str = Field(description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="نقش‌های پرشده از متن؛ در save_text_analysis ذخیره می‌شود",
    )
    discovered: bool = Field(
        default=False,
        description="اگر قالب کاتالوگ نبود و نوع نو از متن ساخته شد",
    )
    type_schema: Optional[DiscourseTypeSchema] = Field(
        default=None,
        description="ساختار نوع کشف‌شده؛ برای کاتالوگ ثابت خالی است",
    )


class IntentHit(BaseModel):
    """نیت گوینده؛ آمادهٔ text_analysis_intents."""

    code: str = Field(description="کد intents مثل complaint یا follow_up")
    name: str = Field(description="نام فارسی نیت")
    is_primary: bool = Field(description="نیت اصلی همین متن")
    mention_text: str = Field(description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="نقش‌های پرشده از متن؛ در save_text_analysis ذخیره می‌شود",
    )


class RhetoricHit(BaseModel):
    """صنعت بیان؛ آمادهٔ text_analysis_rhetorics."""

    code: str = Field(description="کد rhetoric_types مثل irony یا sarcasm")
    name: str = Field(description="نام فارسی صنعت بیان")
    is_primary: bool = Field(description="صنعت اصلی همین متن")
    mention_text: str = Field(description="شاهد کوتاه از متن")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")
    slots: dict[str, str] = Field(
        default_factory=dict,
        description="نقش‌های پرشده از متن؛ ظاهر و مقصود",
    )
    intended_meaning: str = Field(
        default="",
        description="بازنویسیٔ صریح غرض گوینده برای لایه‌های دیگر",
    )


class ExtractSentimentOutput(BaseModel):
    """نتیجه قطبیت و هیجان. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    sentiment: Optional[SentimentHit] = None
    emotions: list[EmotionHit] = Field(default_factory=list)
    emotion_count: int = Field(default=0)


class ExtractDiscourseOutput(BaseModel):
    """نتیجه ژانر / نوع پیام. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    discourses: list[DiscourseHit] = Field(default_factory=list)
    discourse_count: int = Field(default=0)


class ExtractIntentOutput(BaseModel):
    """نتیجه نیت گوینده. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    intents: list[IntentHit] = Field(default_factory=list)
    intent_count: int = Field(default=0)


class ExtractRhetoricOutput(BaseModel):
    """نتیجه صنعت بیان. INSERT نیست."""

    status: str = Field(description="همیشه success در مسیر بدون خطا")
    message: str = Field(description="پیام خوانا برای انسان")
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = Field(description="طول متن پس از نرمال‌سازی")
    rhetorics: list[RhetoricHit] = Field(default_factory=list)
    rhetoric_count: int = Field(default=0)
    intended_meaning: str = Field(
        default="",
        description="بازنویسیٔ صریح غرض؛ برای نیت و ژانر و احساس",
    )
