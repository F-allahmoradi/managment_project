"""اعتبارسنجی ورودی ابزارهای TaskItem."""

from logging_module import logged_step
from validators.common import parse_id, writable_update


def validate_create_task_item(fields: dict) -> dict:
    """ورودی ثبت زیرکار را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_item import CreateTaskItemInput

    return CreateTaskItemInput(**fields).model_dump()


def validate_list_task_items(task_id: int) -> int:
    """شناسه فهرست زیرکارها را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_item import ListTaskItemsInput

    return ListTaskItemsInput(task_id=task_id).task_id


def validate_update_task_item(fields: dict) -> dict:
    """ورودی به‌روزرسانی زیرکار را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_item import UpdateTaskItemInput

    return writable_update(UpdateTaskItemInput(**fields))


def validate_complete_task_item(fields: dict) -> dict:
    """ورودی تیک زدن زیرکار را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_item import CompleteTaskItemInput

    return CompleteTaskItemInput(**fields).model_dump()


def validate_delete_task_item(item_id: int) -> int:
    """شناسه حذف زیرکار را با اسکیما بررسی می‌کند."""
    from schemas.crud.task_item import DeleteTaskItemInput

    return parse_id(DeleteTaskItemInput, item_id)


validate_create_task_item = logged_step("validate")(validate_create_task_item)
validate_list_task_items = logged_step("validate")(validate_list_task_items)
validate_update_task_item = logged_step("validate")(validate_update_task_item)
validate_complete_task_item = logged_step("validate")(validate_complete_task_item)
validate_delete_task_item = logged_step("validate")(validate_delete_task_item)
