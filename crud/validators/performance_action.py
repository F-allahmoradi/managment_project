"""اعتبارسنجی ورودی ابزارهای PerformanceAction."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_performance_action(fields: dict) -> dict:
    """ورودی ثبت تشویق یا تنبیه را با اسکیما بررسی می‌کند."""
    from schemas.crud.performance_action import CreatePerformanceActionInput

    return CreatePerformanceActionInput(**fields).model_dump()


def validate_get_performance_action(row_id: int) -> int:
    """شناسه خواندن اقدام را با اسکیما بررسی می‌کند."""
    from schemas.crud.performance_action import GetPerformanceActionInput

    return parse_id(GetPerformanceActionInput, row_id)


def validate_list_performance_actions(
    user_id=None,
    project_id=None,
    limit=None,
    offset=None,
) -> dict:
    """صفحه‌بندی و فیلتر فهرست اقدامات را با اسکیما بررسی می‌کند."""
    from schemas.crud.performance_action import ListPerformanceActionsInput

    return parse_optional(ListPerformanceActionsInput, user_id=user_id, project_id=project_id, limit=limit, offset=offset)


validate_create_performance_action = logged_step("validate")(
    validate_create_performance_action
)
validate_get_performance_action = logged_step("validate")(
    validate_get_performance_action
)
validate_list_performance_actions = logged_step("validate")(
    validate_list_performance_actions
)
