"""سرویس جدول contents و متادیتای media_files.

متن، صوت، تصویر یا فایل. آپلود واقعی روی S3 نیست؛ storage_key کافی است.
"""

from errors.crud import ContentNotFoundError, InvalidInputError
from logging_module import logged_step
from repository import (
    delete_row_on,
    fetch_content_record,
    fetch_contents_for_actor_records,
    fetch_first,
    insert_row_on,
    run_query,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, ACTION_DELETE, record_audit_on

ALLOWED_KIND_CODES = frozenset({"TEXT", "VOICE", "IMAGE", "FILE"})
_MEDIA_KIND_CODES = frozenset({"VOICE", "IMAGE", "FILE"})


def _not_found_message(content_id: int) -> str:
    return f"محتوا با شناسه {content_id} پیدا نشد"


def _resolve_kind(fields: dict) -> dict:
    """نوع محتوا را از شناسه یا کد/نام seed می‌خواند."""
    kind_id = fields.get("content_kind_id")
    code = fields.get("content_kind")
    if kind_id is not None:
        row = fetch_first("content_kinds", {"id": kind_id})
        if row is None:
            raise InvalidInputError(f"نوع محتوا با شناسه {kind_id} پیدا نشد")
    else:
        row = fetch_first("content_kinds", {"code": code})
        if row is None:
            row = fetch_first("content_kinds", {"name": code})
        if row is None:
            raise InvalidInputError(f"نوع محتوا «{code}» پیدا نشد")
    if row.get("is_active") is False:
        raise InvalidInputError("نوع محتوا غیرفعال است")
    if row["code"] not in ALLOWED_KIND_CODES:
        raise InvalidInputError("نوع محتوا باید TEXT، VOICE، IMAGE یا FILE باشد")
    return row


def fetch_content(content_id: int) -> dict:
    """یک محتوا را با نوع و متادیتای فایل می‌خواند."""
    row = fetch_content_record(content_id)
    if row is None:
        raise ContentNotFoundError(_not_found_message(content_id))
    return row


def insert_content(fields: dict, created_by: int) -> int:
    """متن یا متادیتای صوت، تصویر و فایل را در contents درج می‌کند."""
    kind = _resolve_kind(fields)
    text_body = fields.get("text_body")
    if kind["code"] == "TEXT":
        if text_body is None or not str(text_body).strip():
            raise InvalidInputError("متن برای محتوای TEXT لازم است")
        if fields.get("storage_key") or fields.get("file_size_bytes"):
            raise InvalidInputError("محتوای متن نباید فایل داشته باشد")

        def work_text(connection):
            new_id = insert_row_on(
                connection,
                "contents",
                {
                    "content_kind_id": kind["id"],
                    "text_body": text_body,
                    "created_by_user_id": created_by,
                },
            )
            record_audit_on(
                connection,
                created_by,
                ACTION_CREATE,
                "Content",
                new_id,
                None,
                {"content_kind": kind["code"]},
            )
            return new_id

        return run_query(work_text)

    if kind["code"] not in _MEDIA_KIND_CODES:
        raise InvalidInputError("نوع محتوا باید TEXT، VOICE، IMAGE یا FILE باشد")
    required = (
        fields.get("storage_key"),
        fields.get("original_filename"),
        fields.get("mime_type"),
        fields.get("file_size_bytes"),
    )
    if any(item is None or (isinstance(item, str) and not item.strip()) for item in required):
        raise InvalidInputError("برای این فایل کلید، نام، نوع MIME و اندازه لازم است")

    def work_voice(connection):
        media_id = insert_row_on(
            connection,
            "media_files",
            {
                "storage_key": fields["storage_key"],
                "original_filename": fields["original_filename"],
                "mime_type": fields["mime_type"],
                "file_size_bytes": fields["file_size_bytes"],
                "duration_seconds": fields.get("duration_seconds"),
                "uploaded_by_user_id": created_by,
            },
        )
        new_id = insert_row_on(
            connection,
            "contents",
            {
                "content_kind_id": kind["id"],
                "text_body": text_body,
                "media_file_id": media_id,
                "created_by_user_id": created_by,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Content",
            new_id,
            None,
            {
                "content_kind": kind["code"],
                "media_file_id": media_id,
                "storage_key": fields["storage_key"],
            },
        )
        return new_id

    unique_messages = {
        **unique_messages_for("media_files"),
        **unique_messages_for("contents"),
    }
    return run_query(work_voice, unique_messages)


def fetch_contents_for_actor(actor_id: int, limit: int, offset: int) -> list:
    """محتواهای فعال خود کاربر را از جدید به قدیم برمی‌گرداند."""
    return fetch_contents_for_actor_records(actor_id, limit, offset)


def delete_content(content_id: int, actor_id: int) -> int:
    """محتوا را نرم‌حذف می‌کند؛ ردیف در DB می‌ماند."""
    existing = fetch_content(content_id)

    def work(connection):
        deleted_id = delete_row_on(
            connection,
            "contents",
            content_id,
            ContentNotFoundError,
            _not_found_message(content_id),
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_DELETE,
            "Content",
            deleted_id,
            {
                "content_kind": existing.get("content_kind_code"),
                "media_file_id": existing.get("media_file_id"),
            },
            None,
        )
        return deleted_id

    return run_query(work)


insert_content = logged_step("insert")(insert_content)
fetch_content = logged_step("fetch")(fetch_content)
fetch_contents_for_actor = logged_step("fetch")(fetch_contents_for_actor)
delete_content = logged_step("delete")(delete_content)
