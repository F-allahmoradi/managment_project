"""سرویس عملیات جدول chats.

سازنده هنگام درج عضو chat_members می‌شود.
گفتگوی خصوصی project_id ندارد؛ گفتگوی پروژه باید به پروژه وصل باشد.
"""

from errors.crud import ChatNotFoundError, InvalidInputError
from logging_module import logged_step
from repository import (
    fetch_chat_membership_record,
    fetch_chat_record,
    fetch_chats_for_actor_records,
    fetch_first,
    insert_row_on,
    resolve_lookup_id,
    run_query,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, record_audit_on
from services.project import fetch_project

PROJECT_CHAT_TYPE = "گفتگوی پروژه"
PRIVATE_CHAT_TYPE = "گفتگوی خصوصی"


def _not_found_message(chat_id: int) -> str:
    return f"گفتگو با شناسه {chat_id} پیدا نشد"


def fetch_chat(chat_id: int) -> dict:
    """یک گفتگو را با شناسه می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_chat_record(chat_id)
    if row is None:
        raise ChatNotFoundError(_not_found_message(chat_id))
    return row


def chat_exists(chat_id: int) -> bool:
    """اگر ردیف chats وجود داشته باشد True است."""
    return fetch_first("chats", {"id": chat_id}, columns=("id",)) is not None


def fetch_chat_membership(chat_id: int, user_id: int):
    """عضویت کاربر در گفتگو را برمی‌گرداند یا None."""
    return fetch_chat_membership_record(chat_id, user_id)


def fetch_chats_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """گفتگوهایی را می‌خواند که کاربر عضوشان است."""
    return fetch_chats_for_actor_records(user_id, limit, offset, project_id)


def insert_chat(fields: dict, created_by: int) -> int:
    """گفتگو را درج می‌کند و سازنده را عضو همان گفتگو می‌کند."""
    type_id = resolve_lookup_id(
        "chat_types",
        fields.get("chat_type_id"),
        fields.get("chat_type"),
    )
    type_row = fetch_first("chat_types", {"id": type_id}, columns=("id", "name"))
    type_name = type_row["name"] if type_row else ""
    project_id = fields.get("project_id")
    if type_name == PROJECT_CHAT_TYPE and project_id is None:
        raise InvalidInputError("گفتگوی پروژه باید به یک پروژه وصل باشد")
    if type_name == PRIVATE_CHAT_TYPE and project_id is not None:
        raise InvalidInputError("گفتگوی خصوصی نباید به پروژه وصل باشد")
    if project_id is not None:
        fetch_project(project_id)
    values = {
        "title": fields["title"],
        "chat_type_id": type_id,
        "project_id": project_id,
    }

    def work(connection):
        chat_id = insert_row_on(connection, "chats", values)
        insert_row_on(
            connection,
            "chat_members",
            {"chat_id": chat_id, "user_id": created_by},
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Chat",
            chat_id,
            None,
            {
                "title": values["title"],
                "chat_type_id": type_id,
                "project_id": project_id,
            },
        )
        return chat_id

    return run_query(work, unique_messages_for("chat_members"))


insert_chat = logged_step("insert")(insert_chat)
fetch_chat = logged_step("fetch")(fetch_chat)
fetch_chats_for_actor = logged_step("fetch")(fetch_chats_for_actor)
fetch_chat_membership = logged_step("fetch")(fetch_chat_membership)
