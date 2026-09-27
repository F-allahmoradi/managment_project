"""اعتبارسنجی ورودی ابزارهای پردازش زبانی."""

from logging_module import logged_step
from schemas.input import ExtractNlpInput


def validate_extract_nlp(fields: dict) -> dict:
    """ورودی استخراج را با اسکیما بررسی می‌کند."""
    return ExtractNlpInput(**fields).model_dump()


validate_extract_nlp = logged_step("validate")(validate_extract_nlp)
