"""اعتبارسنجی ورودی ابزارهای ChatMember."""

from logging_module import logged_step


def validate_create_chat_member(fields: dict) -> dict:
    """ورودی افزودن عضو گفتگو را با اسکیما بررسی می‌کند."""
    from schemas.crud.chat_member import CreateChatMemberInput

    return CreateChatMemberInput(**fields).model_dump()


def validate_list_chat_members(chat_id, limit=None, offset=None) -> dict:
    """صفحه‌بندی فهرست اعضای یک گفتگو را با اسکیما بررسی می‌کند."""
    from schemas.crud.chat_member import ListChatMembersInput

    payload = {"chat_id": chat_id}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListChatMembersInput(**payload).model_dump()


validate_create_chat_member = logged_step("validate")(validate_create_chat_member)
validate_list_chat_members = logged_step("validate")(validate_list_chat_members)
