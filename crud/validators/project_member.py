"""اعتبارسنجی ورودی ابزارهای ProjectMember."""

from logging_module import logged_step
from validators.common import writable_update


def validate_create_project_member(fields: dict) -> dict:
    """ورودی افزودن عضو به پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project_member import CreateProjectMemberInput

    return CreateProjectMemberInput(**fields).model_dump()


def validate_list_project_members(
    project_id,
    limit=None,
    offset=None,
) -> dict:
    """ورودی فهرست اعضای پروژه را با اسکیما بررسی می‌کند."""
    from schemas.crud.project_member import ListProjectMembersInput

    payload = {"project_id": project_id}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListProjectMembersInput(**payload).model_dump()


def validate_update_project_member(fields: dict) -> dict:
    """ورودی به‌روزرسانی عضویت را با اسکیما بررسی می‌کند."""
    from schemas.crud.project_member import UpdateProjectMemberInput

    return writable_update(UpdateProjectMemberInput(**fields))


validate_create_project_member = logged_step("validate")(
    validate_create_project_member
)
validate_list_project_members = logged_step("validate")(
    validate_list_project_members
)
validate_update_project_member = logged_step("validate")(
    validate_update_project_member
)
