"""اعتبارسنجی ورودی ابزارهای تحلیل متن."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_save_text_analysis(fields: dict) -> dict:
    """ورودی ذخیره تحلیل را با اسکیما بررسی می‌کند."""
    from schemas.crud.text_analysis import SaveTextAnalysisInput

    return SaveTextAnalysisInput(**fields).model_dump()


def validate_get_text_analysis(analysis_id: int) -> int:
    """شناسه خواندن تحلیل را با اسکیما بررسی می‌کند."""
    from schemas.crud.text_analysis import GetTextAnalysisInput

    return parse_id(GetTextAnalysisInput, analysis_id)


def validate_list_text_analyses(
    source_type=None,
    source_id=None,
    limit=None,
    offset=None,
) -> dict:
    """صفحه‌بندی و فیلتر منبع فهرست تحلیل را با اسکیما بررسی می‌کند."""
    from schemas.crud.text_analysis import ListTextAnalysesInput

    return parse_optional(
        ListTextAnalysesInput,
        source_type=source_type,
        source_id=source_id,
        limit=limit,
        offset=offset,
    )


validate_save_text_analysis = logged_step("validate")(validate_save_text_analysis)
validate_get_text_analysis = logged_step("validate")(validate_get_text_analysis)
validate_list_text_analyses = logged_step("validate")(validate_list_text_analyses)
