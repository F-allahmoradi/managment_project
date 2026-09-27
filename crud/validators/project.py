"""اعتبارسنجی ورودی ابزارهای Project."""

from logging_module import logged_step
from validators.common import parse_id, parse_page, writable_update


def validate_create_project(fields: dict) -> dict:
    """ورودی ثبت پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project import CreateProjectInput

    return CreateProjectInput(**fields).model_dump()


def validate_get_project(project_id: int) -> int:
    """شناسه خواندن پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project import GetProjectInput

    return parse_id(GetProjectInput, project_id)


def validate_list_projects(limit=None, offset=None) -> tuple[int, int]:
    """صفحه‌بندی فهرست پروژه‌ها را با اسکیما بررسی می‌کند."""
    from schemas.crud.project import ListProjectsInput

    return parse_page(ListProjectsInput, limit=limit, offset=offset)


def validate_update_project(fields: dict) -> dict:
    """ورودی به‌روزرسانی پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project import UpdateProjectInput

    return writable_update(UpdateProjectInput(**fields))


def validate_delete_project(project_id: int) -> int:
    """شناسه حذف پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project import GetProjectInput

    return parse_id(GetProjectInput, project_id)


validate_create_project = logged_step("validate")(validate_create_project)
validate_get_project = logged_step("validate")(validate_get_project)
validate_list_projects = logged_step("validate")(validate_list_projects)
validate_update_project = logged_step("validate")(validate_update_project)
validate_delete_project = logged_step("validate")(validate_delete_project)
