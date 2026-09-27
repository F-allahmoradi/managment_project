"""خواندن متن خام گزارش، جلسه یا پیام. INSERT نیست."""

from errors.crud import (
    EmptyTranscriptError,
    InvalidInputError,
    MeetingNotFoundError,
    MessageNotFoundError,
    PermissionDeniedError,
)
from logging_module import logged_step
from auth.gate import require_chat_member
from repository.db import fetch_one
from services.project import fetch_active_membership

from business_logic.config import (
    load_column_config,
    load_discourse_catalog,
    load_intent_catalog,
    load_layer_config,
    load_llm_public,
    load_rhetoric_catalog,
    load_source,
    load_stance_catalog,
    load_topic_catalog,
)

_SOURCE_KEY = "project_texts"

_MEETING_COLUMNS = (
    "id",
    "project_id",
    "manager_user_id",
    "visibility",
    "title",
    "status_name",
    "content_id",
    "content_kind_code",
    "text_body",
    "project_name",
)


def _actor_can_see_meeting(user_id: int, meeting: dict) -> bool:
    """مدیر، شرکت‌کننده، یا عضو پروژهٔ جلسهٔ PROJECT می‌تواند ببیند."""
    if meeting["manager_user_id"] == user_id:
        return True
    if meeting.get("visibility") == "PROJECT" and meeting.get("project_id") is not None:
        if fetch_active_membership(meeting["project_id"], user_id) is not None:
            return True
    found = fetch_one(
        """
        SELECT id
        FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        LIMIT 1
        """,
        [meeting["id"], user_id],
        ("id",),
    )
    return found is not None


@logged_step("fetch")
def fetch_meeting_transcript(meeting_id: int, actor_id: int) -> dict:
    """رونوشت جلسه را می‌خواند؛ متن خالی رد می‌شود."""
    row = fetch_one(
        """
        SELECT m.id, m.project_id, m.manager_user_id, m.visibility, m.title,
               st.name AS status_name, m.content_id,
               k.code AS content_kind_code, c.text_body,
               p.name AS project_name
        FROM meetings m
        JOIN meeting_statuses st ON st.id = m.status_id
        LEFT JOIN contents c ON c.id = m.content_id
        LEFT JOIN content_kinds k ON k.id = c.content_kind_id
        LEFT JOIN projects p ON p.id = m.project_id
        WHERE m.id = %s
        """,
        [meeting_id],
        _MEETING_COLUMNS,
    )
    if row is None:
        raise MeetingNotFoundError(f"جلسه با شناسه {meeting_id} پیدا نشد")
    if not _actor_can_see_meeting(actor_id, row):
        raise PermissionDeniedError("به این جلسه دسترسی ندارید")
    if row.get("content_id") is None:
        raise InvalidInputError("ابتدا جلسه را ضبط کنید")
    body = row.get("text_body")
    if body is None or not str(body).strip():
        raise EmptyTranscriptError("متن منبع خالی است")
    return {
        "source_type": "meeting",
        "source_id": row["id"],
        "table": "contents",
        "column": "text_body",
        "text": str(body).strip(),
        "text_length": len(str(body).strip()),
    }


@logged_step("fetch")
def fetch_message_text(message_id: int, actor_id: int) -> dict:
    """متن پیام را می‌خواند؛ فقط عضو گفتگو."""
    row = fetch_one(
        """
        SELECT m.id, m.chat_id, m.text, c.text_body
        FROM messages m
        LEFT JOIN contents c ON c.id = m.content_id
        WHERE m.id = %s
        """,
        [message_id],
        ("id", "chat_id", "text", "text_body"),
    )
    if row is None:
        raise MessageNotFoundError(f"پیام با شناسه {message_id} پیدا نشد")
    require_chat_member(actor_id, row["chat_id"])
    body = row.get("text") or row.get("text_body")
    if body is None or not str(body).strip():
        raise EmptyTranscriptError("متن منبع خالی است")
    return {
        "source_type": "message",
        "source_id": row["id"],
        "table": "messages",
        "column": "text",
        "text": str(body).strip(),
        "text_length": len(str(body).strip()),
    }


@logged_step("fetch")
def fetch_source_text(source_type: str, source_id: int, actor_id: int) -> dict:
    """متن خام منبع را برمی‌گرداند."""
    if source_type == "meeting":
        return fetch_meeting_transcript(source_id, actor_id)
    if source_type == "message":
        return fetch_message_text(source_id, actor_id)
    raise InvalidInputError("source_type باید meeting یا message باشد")


def get_public_catalog() -> dict:
    """فرادادهٔ عمومی بدون host و رمز."""
    source = load_source()
    columns = load_column_config()
    llm = load_llm_public()
    return {
        "source": _SOURCE_KEY,
        "type": source.get("type"),
        "table": source.get("table") or "entity_mentions",
        "column": source.get("column") or "mention_text",
        "extractor": "llm",
        "model": llm["model"],
        "extractable_fields": list(columns.get("extractable") or []),
        "layers": load_layer_config(),
        "topics": load_topic_catalog(),
        "stance": load_stance_catalog(),
        "discourses": load_discourse_catalog(),
        "intents": load_intent_catalog(),
        "rhetorics": load_rhetoric_catalog(),
        "enums": columns.get("enums") or {},
        "ranges": columns.get("ranges") or {},
        "description": source.get("description"),
        "writes_postgres": False,
    }
