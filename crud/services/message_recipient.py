"""سرویس گیرندهٔ پیام: قانون XOR قبل از INSERT.

هر ردیف دقیقاً یکی از user یا external_contact است.
کاربر گیرنده باید عضو همان گفتگو باشد. مخاطب خارجی عضو چت نیست.
"""

from errors.crud import InvalidInputError, MessageNotFoundError
from logging_module import logged_step
from repository import (
    fetch_first,
    fetch_message_recipients_records,
    insert_row,
)
from services.audit_log import ACTION_CREATE, record_audit
from services.chat import fetch_chat_membership
from services.external_contact import fetch_external_contact
from services.user import fetch_user


def assert_one_target(user_id, external_contact_id) -> None:
    """اگر هر دو پر یا هر دو خالی باشند قبل از INSERT خطا می‌دهد."""
    has_user = user_id is not None
    has_external = external_contact_id is not None
    if has_user == has_external:
        raise InvalidInputError(
            "گیرنده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
        )


def validate_recipient_target(chat_id: int, user_id, external_contact_id) -> dict:
    """هدف گیرنده را با XOR و وجود ردیف می‌سنجد و فیلدهای INSERT را برمی‌گرداند."""
    assert_one_target(user_id, external_contact_id)
    if user_id is not None:
        user = fetch_user(user_id)
        if not user["is_active"]:
            raise InvalidInputError("کاربر غیرفعال نمی‌تواند گیرنده باشد")
        if fetch_chat_membership(chat_id, user_id) is None:
            raise InvalidInputError("گیرندهٔ کاربر باید عضو همین گفتگو باشد")
        return {"user_id": user_id, "external_contact_id": None}
    contact = fetch_external_contact(external_contact_id)
    if not contact["is_active"]:
        raise InvalidInputError("مخاطب خارجی غیرفعال است")
    return {"user_id": None, "external_contact_id": external_contact_id}


def fetch_message_recipients(message_id: int, limit: int, offset: int) -> list:
    """گیرنده‌های یک پیام را می‌خواند."""
    row = fetch_first("messages", {"id": message_id}, columns=("id",))
    if row is None:
        raise MessageNotFoundError(f"پیام با شناسه {message_id} پیدا نشد")
    return fetch_message_recipients_records(message_id, limit, offset)


def insert_message_recipient(fields: dict, actor_id=None) -> int:
    """یک گیرنده با قانون XOR به پیام موجود اضافه می‌کند."""
    assert_one_target(fields.get("user_id"), fields.get("external_contact_id"))
    message = fetch_first(
        "messages",
        {"id": fields["message_id"]},
        columns=("id", "chat_id"),
    )
    if message is None:
        raise MessageNotFoundError(
            f"پیام با شناسه {fields['message_id']} پیدا نشد"
        )
    prepared = validate_recipient_target(
        message["chat_id"],
        fields.get("user_id"),
        fields.get("external_contact_id"),
    )
    new_id = insert_row(
        "message_recipients",
        {
            "message_id": fields["message_id"],
            "user_id": prepared["user_id"],
            "external_contact_id": prepared["external_contact_id"],
        },
    )
    record_audit(
        actor_id,
        ACTION_CREATE,
        "MessageRecipient",
        new_id,
        None,
        {
            "message_id": fields["message_id"],
            "user_id": prepared["user_id"],
            "external_contact_id": prepared["external_contact_id"],
        },
    )
    return new_id


assert_one_target = logged_step("validate")(assert_one_target)
insert_message_recipient = logged_step("insert")(insert_message_recipient)
fetch_message_recipients = logged_step("fetch")(fetch_message_recipients)
