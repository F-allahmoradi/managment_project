"""اعتبارسنجی ورودی ابزارهای Role."""

from logging_module import logged_step
from validators.common import parse_id, parse_page, writable_update


def validate_create_role(fields: dict) -> dict:
    """ورودی ثبت نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role import CreateRoleInput

    return CreateRoleInput(**fields).model_dump()


def validate_get_role(role_id: int) -> int:
    """شناسه خواندن نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role import GetRoleInput

    return parse_id(GetRoleInput, role_id)


def validate_list_roles(limit=None, offset=None) -> tuple[int, int]:
    """صفحه‌بندی فهرست نقش‌ها را با اسکیما بررسی می‌کند."""
    from schemas.crud.role import ListRolesInput

    return parse_page(ListRolesInput, limit=limit, offset=offset)


def validate_update_role(fields: dict) -> dict:
    """ورودی به‌روزرسانی نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role import UpdateRoleInput

    return writable_update(UpdateRoleInput(**fields))


def validate_delete_role(role_id: int) -> int:
    """شناسه حذف نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role import DeleteRoleInput

    return parse_id(DeleteRoleInput, role_id)


validate_create_role = logged_step("validate")(validate_create_role)
validate_get_role = logged_step("validate")(validate_get_role)
validate_list_roles = logged_step("validate")(validate_list_roles)
validate_update_role = logged_step("validate")(validate_update_role)
validate_delete_role = logged_step("validate")(validate_delete_role)
