"""اعتبارسنجی ورودی ابزارهای Message."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_message(fields: dict) -> dict:
    """ورودی ارسال پیام را با اسکیما بررسی می‌کند."""
    from schemas.crud.message import CreateMessageInput

    return CreateMessageInput(**fields).model_dump()


def validate_get_message(message_id: int) -> int:
    """شناسه خواندن پیام را با اسکیما بررسی می‌کند."""
    from schemas.crud.message import GetMessageInput

    return parse_id(GetMessageInput, message_id)


def validate_list_messages(chat_id=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر گفتگوی فهرست پیام‌ها را با اسکیما بررسی می‌کند."""
    from schemas.crud.message import ListMessagesInput

    return parse_optional(ListMessagesInput, chat_id=chat_id, limit=limit, offset=offset)


validate_create_message = logged_step("validate")(validate_create_message)
validate_get_message = logged_step("validate")(validate_get_message)
validate_list_messages = logged_step("validate")(validate_list_messages)
