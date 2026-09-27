"""سرویس ممیزی: چه کسی کدام موجودیت را عوض کرد.

نوشتن ممیزی اثر جانبی ابزارهای قبلی است؛ ابزار create_audit_log
برای کاربر عادی ثبت نمی‌شود. با execution_logs فرق دارد.
"""

from psycopg2.extras import Json

from errors.crud import AuditLogNotFoundError, InvalidInputError
from logging_module import logged_step
from repository import (
    fetch_audit_log_record,
    fetch_audit_logs_records,
    insert_row,
    insert_row_on,
)
from repository.db import json_safe

ACTION_CREATE = "Create"
ACTION_UPDATE = "Update"
ACTION_DELETE = "Delete"


def _not_found_message(row_id: int) -> str:
    return f"ممیزی با شناسه {row_id} پیدا نشد"


def _jsonb(payload):
    """دیکشنری را برای ستون jsonb آماده می‌کند؛ None یعنی SQL NULL."""
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise InvalidInputError("مقدار ممیزی باید شیء JSON باشد")
    cleaned = {key: json_safe(value) for key, value in payload.items()}
    return Json(cleaned)


def record_audit_on(
    connection,
    actor_id,
    action: str,
    entity: str,
    entity_id,
    old_value=None,
    new_value=None,
):
    """یک ردیف audit_logs روی اتصال باز درج می‌کند؛ بدون عامل رد می‌شود."""
    if actor_id is None:
        return None
    fields = {
        "user_id": actor_id,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
    }
    encoded_old = _jsonb(old_value)
    encoded_new = _jsonb(new_value)
    if encoded_old is not None:
        fields["old_value"] = encoded_old
    if encoded_new is not None:
        fields["new_value"] = encoded_new
    return insert_row_on(connection, "audit_logs", fields)


def record_audit(
    actor_id,
    action: str,
    entity: str,
    entity_id,
    old_value=None,
    new_value=None,
):
    """یک ردیف ممیزی درج می‌کند؛ اگر عامل نباشد هیچ نمی‌نویسد."""
    if actor_id is None:
        return None
    fields = {
        "user_id": actor_id,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
    }
    encoded_old = _jsonb(old_value)
    encoded_new = _jsonb(new_value)
    if encoded_old is not None:
        fields["old_value"] = encoded_old
    if encoded_new is not None:
        fields["new_value"] = encoded_new
    return insert_row("audit_logs", fields)


def fetch_audit_log(row_id: int) -> dict:
    """یک ردیف ممیزی را با شناسه می‌خواند."""
    row = fetch_audit_log_record(row_id)
    if row is None:
        raise AuditLogNotFoundError(_not_found_message(row_id))
    return row


def fetch_audit_logs(
    limit: int,
    offset: int,
    entity=None,
    entity_id=None,
    user_id=None,
) -> list:
    """فهرست ممیزی را با فیلتر اختیاری می‌خواند."""
    return fetch_audit_logs_records(
        limit,
        offset,
        entity=entity,
        entity_id=entity_id,
        user_id=user_id,
    )


record_audit = logged_step("insert")(record_audit)
fetch_audit_log = logged_step("fetch")(fetch_audit_log)
fetch_audit_logs = logged_step("fetch")(fetch_audit_logs)
