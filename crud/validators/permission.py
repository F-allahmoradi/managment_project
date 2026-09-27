"""اعتبارسنجی ورودی ابزارهای Permission."""

from logging_module import logged_step
from validators.common import parse_page


def validate_create_permission(fields: dict) -> dict:
    """ورودی ثبت مجوز را با اسکیما بررسی می‌کند."""
    from schemas.crud.permission import CreatePermissionInput

    return CreatePermissionInput(**fields).model_dump()


def validate_list_permissions(limit=None, offset=None) -> tuple[int, int]:
    """صفحه‌بندی فهرست مجوزها را با اسکیما بررسی می‌کند."""
    from schemas.crud.permission import ListPermissionsInput

    return parse_page(ListPermissionsInput, limit=limit, offset=offset)


validate_create_permission = logged_step("validate")(validate_create_permission)
validate_list_permissions = logged_step("validate")(validate_list_permissions)
