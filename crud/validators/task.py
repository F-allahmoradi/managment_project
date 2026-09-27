"""اعتبارسنجی ورودی ابزارهای Task."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional, writable_update


def validate_create_task(fields: dict) -> dict:
    """ورودی ثبت وظیفه را با اسکیما بررسی می‌کند."""
    from schemas.crud.task import CreateTaskInput

    return CreateTaskInput(**fields).model_dump()


def validate_get_task(task_id: int) -> int:
    """شناسه خواندن وظیفه را با اسکیما بررسی می‌کند."""
    from schemas.crud.task import GetTaskInput

    return parse_id(GetTaskInput, task_id)


def validate_list_tasks(project_id=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر پروژهٔ فهرست وظایف را با اسکیما بررسی می‌کند."""
    from schemas.crud.task import ListTasksInput

    return parse_optional(ListTasksInput, project_id=project_id, limit=limit, offset=offset)


def validate_update_task(fields: dict) -> dict:
    """ورودی به‌روزرسانی وظیفه را با اسکیما بررسی می‌کند."""
    from schemas.crud.task import UpdateTaskInput

    return writable_update(UpdateTaskInput(**fields))


def validate_delete_task(task_id: int) -> int:
    """شناسه حذف وظیفه را با اسکیما بررسی می‌کند."""
    from schemas.crud.task import GetTaskInput

    return parse_id(GetTaskInput, task_id)


validate_create_task = logged_step("validate")(validate_create_task)
validate_get_task = logged_step("validate")(validate_get_task)
validate_list_tasks = logged_step("validate")(validate_list_tasks)
validate_update_task = logged_step("validate")(validate_update_task)
validate_delete_task = logged_step("validate")(validate_delete_task)
