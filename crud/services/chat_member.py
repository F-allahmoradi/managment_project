"""سرویس عملیات جدول chat_members.

فقط کاربر سامانه عضو گفتگو می‌شود؛ مخاطب خارجی اینجا نیست.
اگر گفتگو به پروژه وصل باشد، عضو جدید باید عضو فعال همان پروژه باشد.
"""

from errors.crud import ChatMemberNotFoundError, InvalidInputError
from logging_module import logged_step
from repository import (
    fetch_chat_member_record,
    fetch_chat_members_records,
    insert_row,
)
from services.audit_log import ACTION_CREATE, record_audit
from services.chat import fetch_chat, fetch_chat_membership
from services.project import fetch_active_membership
from services.user import fetch_user


def _not_found_message(row_id: int) -> str:
    return f"عضویت گفتگو با شناسه {row_id} پیدا نشد"


def fetch_chat_member(row_id: int) -> dict:
    """یک عضویت گفتگو را با شناسه می‌خواند."""
    row = fetch_chat_member_record(row_id)
    if row is None:
        raise ChatMemberNotFoundError(_not_found_message(row_id))
    return row


def fetch_chat_members(chat_id: int, limit: int, offset: int) -> list:
    """اعضای یک گفتگو را با صفحه‌بندی می‌خواند."""
    fetch_chat(chat_id)
    return fetch_chat_members_records(chat_id, limit, offset)


def insert_chat_member(fields: dict, actor_id=None) -> int:
    """یک کاربر سامانه را به گفتگو اضافه می‌کند."""
    chat = fetch_chat(fields["chat_id"])
    user = fetch_user(fields["user_id"])
    if not user["is_active"]:
        raise InvalidInputError("کاربر غیرفعال را نمی‌توان به گفتگو اضافه کرد")
    if fetch_chat_membership(chat["id"], fields["user_id"]) is not None:
        raise InvalidInputError("این کاربر از قبل عضو گفتگو است")
    project_id = chat.get("project_id")
    if project_id is not None:
        membership = fetch_active_membership(project_id, fields["user_id"])
        if membership is None:
            raise InvalidInputError("کاربر باید عضو فعال پروژهٔ همین گفتگو باشد")
    new_id = insert_row(
        "chat_members",
        {"chat_id": fields["chat_id"], "user_id": fields["user_id"]},
    )
    record_audit(
        actor_id,
        ACTION_CREATE,
        "ChatMember",
        new_id,
        None,
        {"chat_id": fields["chat_id"], "user_id": fields["user_id"]},
    )
    return new_id


insert_chat_member = logged_step("insert")(insert_chat_member)
fetch_chat_member = logged_step("fetch")(fetch_chat_member)
fetch_chat_members = logged_step("fetch")(fetch_chat_members)
