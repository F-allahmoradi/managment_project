"""حذف نرم: هیچ DELETE فیزیکی از مسیر CRUD اجرا نمی‌شود."""

from psycopg2 import sql

from errors.crud import InvalidInputError
from repository.columns import load_column_config
from repository.engine import fetch_first_on, update_row_on

CANCELLED_STATUS_NAME = "لغو شده"


def _resolve_status_id(connection, lookup_entity: str, status_name: str) -> int:
    row = fetch_first_on(
        connection,
        lookup_entity,
        {"name": status_name},
        columns=("id", "name"),
    )
    if row is None:
        raise InvalidInputError(f"وضعیت «{status_name}» در {lookup_entity} پیدا نشد")
    return int(row["id"])


def soft_delete_row_on(
    connection,
    entity_key: str,
    row_id: int,
    not_found_error,
    not_found_message: str,
) -> int:
    """ردیف را غیرفعال یا لغو می‌کند و شناسه را برمی‌گرداند."""
    cfg = load_column_config(entity_key)
    spec = cfg.get("soft_delete")
    if not spec:
        raise InvalidInputError(
            f"حذف فیزیکی برای {entity_key} مجاز نیست؛ soft_delete در columns.yaml تعریف نشده"
        )
    strategy = spec.get("strategy")
    if strategy == "is_active":
        existing = fetch_first_on(connection, entity_key, {"id": row_id}, columns=("id", "is_active"))
        if existing is None:
            raise not_found_error(not_found_message)
        if existing.get("is_active") is False:
            return row_id
        return update_row_on(
            connection,
            entity_key,
            {"id": row_id, "is_active": False},
            not_found_error,
            not_found_message,
        )
    if strategy == "status":
        status_column = spec["status_column"]
        lookup_entity = spec["status_lookup"]
        status_name = spec.get("status_name") or CANCELLED_STATUS_NAME
        status_id = _resolve_status_id(connection, lookup_entity, status_name)
        allowed = set(cfg.get("allowed") or []) | set(cfg.get("writable") or [])
        if status_column not in allowed:
            raise InvalidInputError(f"ستون وضعیت {status_column} برای {entity_key} مجاز نیست")
        existing = fetch_first_on(connection, entity_key, {"id": row_id}, columns=("id", status_column))
        if existing is None:
            raise not_found_error(not_found_message)
        if existing.get(status_column) == status_id:
            return row_id
        return update_row_on(
            connection,
            entity_key,
            {"id": row_id, status_column: status_id},
            not_found_error,
            not_found_message,
        )
    raise InvalidInputError(f"استراتژی soft_delete نامعتبر برای {entity_key}")


def project_row_is_cancelled(row: dict) -> bool:
    return row.get("project_status_name") == CANCELLED_STATUS_NAME


def task_row_is_cancelled(row: dict) -> bool:
    return row.get("status_name") == CANCELLED_STATUS_NAME
