"""اعتبارسنجی ورودی اتصال نقش به کاربر."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_user_role(fields: dict) -> dict:
    """ورودی دادن نقش به کاربر را با اسکیما بررسی می‌کند."""
    from schemas.crud.user_role import CreateUserRoleInput

    return CreateUserRoleInput(**fields).model_dump()


def validate_delete_user_role(row_id: int) -> int:
    """شناسه گرفتن نقش از کاربر را با اسکیما بررسی می‌کند."""
    from schemas.crud.user_role import DeleteUserRoleInput

    return parse_id(DeleteUserRoleInput, row_id)


def validate_list_user_roles(user_id=None, limit=None, offset=None) -> dict:
    """ورودی فهرست نقش‌های کاربر را با اسکیما بررسی می‌کند."""
    from schemas.crud.user_role import ListUserRolesInput

    return parse_optional(ListUserRolesInput, user_id=user_id, limit=limit, offset=offset)


validate_create_user_role = logged_step("validate")(validate_create_user_role)
validate_delete_user_role = logged_step("validate")(validate_delete_user_role)
validate_list_user_roles = logged_step("validate")(validate_list_user_roles)
