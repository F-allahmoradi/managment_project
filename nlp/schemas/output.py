"""مدل‌های خروجی فکت، نقل‌قول و قاب مسئله. INSERT نیست."""

from typing import Optional

from pydantic import BaseModel, Field


class FactHit(BaseModel):
    """یک فکت مقید به شاهد از متن."""

    fact_id: str = Field(description="شناسه کوتاه داخل همین پاسخ")
    kind: str = Field(description="quantity یا condition یا change یا cause یا status")
    kind_name: str = Field(description="نام فارسی نوع فکت")
    name: str = Field(description="برچسب کوتاه فکت")
    value: Optional[float] = Field(
        default=None,
        description="عدد اگر نوع مقدار باشد",
    )
    unit: Optional[str] = Field(default=None, description="کد واحد مثل percent")
    unit_name: Optional[str] = Field(default=None, description="نام فارسی واحد")
    role: str = Field(
        default="none",
        description="نقش مقدار: total یا part یا remainder یا none",
    )
    effect: str = Field(default="", description="معلول اگر نوع علت باشد")
    previous: str = Field(default="", description="وضعیت قبل اگر نوع تغییر باشد")
    current: str = Field(default="", description="وضعیت بعد اگر نوع تغییر باشد")
    grounding: str = Field(description="explicit یا derived")
    grounding_name: str = Field(description="نام فارسی صراحت")
    derivation: str = Field(
        default="",
        description="subtract یا add یا remainder یا from_evidence",
    )
    source_ids: list[str] = Field(
        default_factory=list,
        description="شناسه فکت‌های منبع برای استنتاج عددی",
    )
    mention_text: str = Field(description="شاهد اصلی از متن")
    start_offset: int = Field(default=-1, description="اندیس شروع شاهد در متن نرمال")
    end_offset: int = Field(default=-1, description="اندیس پایان شاهد در متن نرمال")
    evidence_texts: list[str] = Field(
        default_factory=list,
        description="شاهدهای کمکی که همه باید در متن باشند",
    )
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class QuoteHit(BaseModel):
    """نقل‌قول مستقیم یا غیرمستقیم."""

    mode: str = Field(description="direct یا indirect")
    mode_name: str = Field(description="نام فارسی شیوه نقل")
    attributed_to: str = Field(description="گویندهٔ جمله داخلی")
    quoted_text: str = Field(description="تکهٔ نسبت‌داده‌شده از متن")
    mention_text: str = Field(description="شاهد فعل نقل مثل گفت")
    start_offset: int = Field(default=-1)
    end_offset: int = Field(default=-1)
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class IssueFrameHit(BaseModel):
    """کارت مسئله برای اتصال بعدی به جدول issues. INSERT نیست."""

    title: str = Field(description="عنوان کوتاه مسئله")
    unit: str = Field(default="", description="واحد درگیر اگر در متن باشد")
    process: str = Field(default="", description="کد فرآیند از کاتالوگ")
    process_name: str = Field(default="", description="نام فارسی فرآیند")
    scope: str = Field(description="کد محدوده")
    scope_name: str = Field(description="نام فارسی محدوده")
    about: str = Field(default="", description="شاهد کوتاه موضوع از متن")
    mention_text: str = Field(default="", description="شاهد اصلی")
    confidence: float = Field(description="اطمینان بین ۰ و ۱")


class ExtractFactsOutput(BaseModel):
    """نتیجه فکت و صراحت. INSERT نیست."""

    status: str
    message: str
    source: str = Field(description="کلید منبع؛ project_texts")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = 0
    explicitness: str = Field(
        description="explicit یا derived یا none",
    )
    explicitness_name: str = Field(description="نام فارسی صراحت کل متن")
    facts: list[FactHit] = Field(default_factory=list)
    fact_count: int = 0
    dropped_count: int = Field(
        default=0,
        description="تعداد ادعای مدل که به‌خاطر نبود شاهد یا حساب غلط حذف شد",
    )


class ExtractQuotesOutput(BaseModel):
    """نتیجه نقل‌قول. INSERT نیست."""

    status: str
    message: str
    source: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = 0
    quotes: list[QuoteHit] = Field(default_factory=list)
    quote_count: int = 0


class ExtractFrameOutput(BaseModel):
    """نتیجه قاب مسئله. INSERT نیست."""

    status: str
    message: str
    source: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    text_length: int = 0
    frame: Optional[IssueFrameHit] = None
