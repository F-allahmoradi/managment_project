"""اعتبارسنجی ورودی ابزارهای MessageRecipient."""

from logging_module import logged_step


def validate_create_message_recipient(fields: dict) -> dict:
    """ورودی افزودن گیرنده را با اسکیما بررسی می‌کند؛ XOR در مدل است."""
    from schemas.crud.message_recipient import CreateMessageRecipientInput

    return CreateMessageRecipientInput(**fields).model_dump()


def validate_list_message_recipients(message_id, limit=None, offset=None) -> dict:
    """صفحه‌بندی فهرست گیرنده‌های یک پیام را با اسکیما بررسی می‌کند."""
    from schemas.crud.message_recipient import ListMessageRecipientsInput

    payload = {"message_id": message_id}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListMessageRecipientsInput(**payload).model_dump()


validate_create_message_recipient = logged_step("validate")(
    validate_create_message_recipient
)
validate_list_message_recipients = logged_step("validate")(
    validate_list_message_recipients
)
