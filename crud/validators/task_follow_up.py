"""اعتبارسنجی ورودی ابزارهای TaskFollowUp."""

from logging_module import logged_step
from validators.common import parse_id


def validate_create_task_follow_up(fields: dict) -> dict:
    """ورودی ثبت پیگیری را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_follow_up import CreateTaskFollowUpInput

    return CreateTaskFollowUpInput(**fields).model_dump()


def validate_get_task_follow_up(follow_up_id: int) -> int:
    """شناسه خواندن پیگیری را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_follow_up import GetTaskFollowUpInput

    return parse_id(GetTaskFollowUpInput, follow_up_id)


def validate_list_task_follow_ups(task_id, limit=None, offset=None) -> dict:
    """ورودی فهرست پیگیری‌های یک وظیفه را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_follow_up import ListTaskFollowUpsInput

    payload = {"task_id": task_id}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListTaskFollowUpsInput(**payload).model_dump()


validate_create_task_follow_up = logged_step("validate")(
    validate_create_task_follow_up
)
validate_get_task_follow_up = logged_step("validate")(validate_get_task_follow_up)
validate_list_task_follow_ups = logged_step("validate")(
    validate_list_task_follow_ups
)
