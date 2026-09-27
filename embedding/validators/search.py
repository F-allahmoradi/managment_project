"""اعتبارسنجی ورودی ابزارهای امبدینگ و جستجو."""

from logging_module import logged_step
from schemas.input import (
    IndexPendingInput,
    IndexTextAnalysisInput,
    SearchSimilarInput,
)


def validate_index_text_analysis(analysis_id: int) -> int:
    """شناسه ایندکس را با اسکیما بررسی می‌کند."""
    return IndexTextAnalysisInput(analysis_id=analysis_id).analysis_id


def validate_index_pending(limit: int) -> int:
    """سقف ایندکس باقی‌مانده را بررسی می‌کند."""
    return IndexPendingInput(limit=limit).limit


def validate_search_similar(
    query: str,
    kinds=None,
    source_type=None,
    limit: int = 8,
) -> dict:
    """ورودی جستجوی مشابه را بررسی می‌کند."""
    return SearchSimilarInput(
        query=query,
        kinds=kinds,
        source_type=source_type,
        limit=limit,
    ).model_dump()


validate_index_text_analysis = logged_step("validate")(validate_index_text_analysis)
validate_index_pending = logged_step("validate")(validate_index_pending)
validate_search_similar = logged_step("validate")(validate_search_similar)
