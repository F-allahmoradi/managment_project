"""اعتبارسنجی ورودی ابزار استخراج موجودیت."""

from logging_module import logged_step
from schemas.input import ExtractEntitiesInput


def validate_extract_entities(fields: dict) -> dict:
    """ورودی استخراج را با اسکیما بررسی می‌کند."""
    return ExtractEntitiesInput(**fields).model_dump()


validate_extract_entities = logged_step("validate")(validate_extract_entities)
