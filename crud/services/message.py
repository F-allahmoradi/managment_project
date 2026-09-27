"""سرویس عملیات جدول messages.

متن در text است؛ content_id در این گام نوشته نمی‌شود.
create می‌تواند گیرنده‌ها را همان لحظه در message_recipients بسازد.
حداقل یک گیرنده لازم است. XOR روی هر ردیف گیرنده است.
گفتگوی پروژه: فرستنده عضو فعال پروژه است؛ تسک همان پروژه اختیاری است.
گفتگوی خصوصی: بدون تسک؛ فرستنده عضو همان گفتگو است.
"""

from errors.crud import InvalidInputError, MessageNotFoundError
from logging_module import logged_step
from repository import (
    fetch_first,
    fetch_message_record,
    fetch_messages_for_actor_records,
    insert_row_on,
    run_query,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, record_audit_on
from services.chat import fetch_chat
from services.message_recipient import validate_recipient_target
from services.project import fetch_active_membership
from services.task import fetch_task


def _not_found_message(message_id: int) -> str:
    return f"پیام با شناسه {message_id} پیدا نشد"


def _require_text(text) -> str:
    """متن پیام در این گام الزامی است چون content_id خالی می‌ماند."""
    if text is None or not str(text).strip():
        raise InvalidInputError("متن پیام خالی مجاز نیست")
    return text


def _prepare_message_task(chat: dict, task_id, sender_user_id: int):
    """تسک اختیاری گفتگوی پروژه را می‌سنجد؛ گفتگوی خصوصی تسک ندارد."""
    project_id = chat.get("project_id")
    if project_id is None:
        if task_id is not None:
            raise InvalidInputError("گفتگوی خصوصی نباید به وظیفه وصل باشد")
        return None
    if fetch_active_membership(project_id, sender_user_id) is None:
        raise InvalidInputError("فرستنده باید عضو فعال همین پروژه باشد")
    if task_id is None:
        return None
    task = fetch_task(task_id)
    if task["project_id"] != project_id:
        raise InvalidInputError("تسک باید در همان پروژهٔ گفتگو باشد")
    return task


def fetch_message(message_id: int) -> dict:
    """یک پیام را با شناسه می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_message_record(message_id)
    if row is None:
        raise MessageNotFoundError(_not_found_message(message_id))
    return row


def fetch_message_chat_id(message_id: int) -> int:
    """شناسه گفتگوی یک پیام را برمی‌گرداند."""
    row = fetch_first("messages", {"id": message_id}, columns=("chat_id",))
    if row is None:
        raise MessageNotFoundError(_not_found_message(message_id))
    return row["chat_id"]


def fetch_messages_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    chat_id=None,
) -> list:
    """پیام‌های گفتگوهایی را می‌خواند که کاربر عضوشان است."""
    return fetch_messages_for_actor_records(user_id, limit, offset, chat_id)


def insert_message(fields: dict, sender_user_id: int) -> int:
    """پیام متنی و گیرنده‌های همان لحظه را در یک تراکنش درج می‌کند."""
    chat = fetch_chat(fields["chat_id"])
    text = _require_text(fields.get("text"))
    task = _prepare_message_task(chat, fields.get("task_id"), sender_user_id)
    recipients = []
    if fields.get("recipient_user_id") is not None:
        recipients.append(
            validate_recipient_target(
                chat["id"],
                fields["recipient_user_id"],
                None,
            )
        )
    if fields.get("recipient_external_contact_id") is not None:
        recipients.append(
            validate_recipient_target(
                chat["id"],
                None,
                fields["recipient_external_contact_id"],
            )
        )
    if not recipients:
        raise InvalidInputError("حداقل یک گیرنده لازم است")
    values = {
        "chat_id": chat["id"],
        "sender_user_id": sender_user_id,
        "text": text,
    }
    if task is not None:
        values["task_id"] = task["id"]

    def work(connection):
        message_id = insert_row_on(
            connection,
            "messages",
            values,
        )
        for recipient in recipients:
            insert_row_on(
                connection,
                "message_recipients",
                {
                    "message_id": message_id,
                    "user_id": recipient["user_id"],
                    "external_contact_id": recipient["external_contact_id"],
                },
            )
        record_audit_on(
            connection,
            sender_user_id,
            ACTION_CREATE,
            "Message",
            message_id,
            None,
            {
                "chat_id": chat["id"],
                "task_id": None if task is None else task["id"],
                "project_id": chat["project_id"],
            },
        )
        return message_id

    unique_messages = {
        **unique_messages_for("messages"),
        **unique_messages_for("message_recipients"),
    }
    return run_query(work, unique_messages)


insert_message = logged_step("insert")(insert_message)
fetch_message = logged_step("fetch")(fetch_message)
fetch_message_chat_id = logged_step("fetch")(fetch_message_chat_id)
fetch_messages_for_actor = logged_step("fetch")(fetch_messages_for_actor)
