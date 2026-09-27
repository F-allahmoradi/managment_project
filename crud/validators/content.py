"""اعتبارسنجی ورودی ابزارهای Content."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_content(fields: dict) -> dict:
    """ورودی ثبت محتوا را با اسکیما بررسی می‌کند."""
    from schemas.crud.content import CreateContentInput

    return CreateContentInput(**fields).model_dump()


def validate_get_content(content_id: int) -> int:
    """شناسه خواندن محتوا را با اسکیما بررسی می‌کند."""
    from schemas.crud.content import GetContentInput

    return parse_id(GetContentInput, content_id)


def validate_delete_content(content_id: int) -> int:
    """شناسه حذف محتوا را با اسکیما بررسی می‌کند."""
    from schemas.crud.content import DeleteContentInput

    return parse_id(DeleteContentInput, content_id)


def validate_list_contents(limit=None, offset=None) -> dict:
    """صفحه‌بندی فهرست محتوا را بررسی می‌کند."""
    from schemas.crud.content import ListContentsInput

    return parse_optional(ListContentsInput, limit=limit, offset=offset)


validate_create_content = logged_step("validate")(validate_create_content)
validate_get_content = logged_step("validate")(validate_get_content)
validate_delete_content = logged_step("validate")(validate_delete_content)
validate_list_contents = logged_step("validate")(validate_list_contents)
