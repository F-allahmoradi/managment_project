"""اعتبارسنجی ورودی اتصال مجوز به نقش."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_role_permission(fields: dict) -> dict:
    """ورودی دادن مجوز به نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role_permission import CreateRolePermissionInput

    return CreateRolePermissionInput(**fields).model_dump()


def validate_delete_role_permission(row_id: int) -> int:
    """شناسه گرفتن مجوز از نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role_permission import DeleteRolePermissionInput

    return parse_id(DeleteRolePermissionInput, row_id)


def validate_list_role_permissions(role_id=None, limit=None, offset=None) -> dict:
    """ورودی فهرست مجوزهای نقش را با اسکیما بررسی می‌کند."""
    from schemas.crud.role_permission import ListRolePermissionsInput

    return parse_optional(ListRolePermissionsInput, role_id=role_id, limit=limit, offset=offset)


validate_create_role_permission = logged_step("validate")(validate_create_role_permission)
validate_delete_role_permission = logged_step("validate")(validate_delete_role_permission)
validate_list_role_permissions = logged_step("validate")(validate_list_role_permissions)
