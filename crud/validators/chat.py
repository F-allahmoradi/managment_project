"""اعتبارسنجی ورودی ابزارهای Chat."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_chat(fields: dict) -> dict:
    """ورودی ساخت گفتگو را با اسکیما بررسی می‌کند."""
    from schemas.crud.chat import CreateChatInput

    return CreateChatInput(**fields).model_dump()


def validate_get_chat(chat_id: int) -> int:
    """شناسه خواندن گفتگو را با اسکیما بررسی می‌کند."""
    from schemas.crud.chat import GetChatInput

    return parse_id(GetChatInput, chat_id)


def validate_list_chats(project_id=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر پروژهٔ فهرست گفتگوها را با اسکیما بررسی می‌کند."""
    from schemas.crud.chat import ListChatsInput

    return parse_optional(ListChatsInput, project_id=project_id, limit=limit, offset=offset)


validate_create_chat = logged_step("validate")(validate_create_chat)
validate_get_chat = logged_step("validate")(validate_get_chat)
validate_list_chats = logged_step("validate")(validate_list_chats)
