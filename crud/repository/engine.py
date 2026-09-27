"""موتور SQL مشترک: INSERT / SELECT / UPDATE و حذف نرم یک‌بار این‌جا است.

نام جدول و ستون از columns.yaml می‌آید. قانون دامنه اینجا نیست.
"""

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from errors.crud import InvalidInputError
from repository.columns import load_column_config, unique_messages_for
from repository.db import json_safe, public_record, run_query


def _writable_names(cfg: dict) -> list:
    """ستون‌های قابل‌نوشتن را از YAML برمی‌گرداند."""
    if cfg.get("writable"):
        return list(cfg["writable"])
    readonly = set(cfg.get("readonly") or [])
    return [name for name in cfg["allowed"] if name not in readonly]


def _allowed_names(cfg: dict) -> list:
    allowed = list(cfg.get("allowed") or [])
    if not allowed:
        raise InvalidInputError("هیچ ستون مجازی برای خواندن تعریف نشده")
    return allowed


def _collect_writable(entity_key: str, fields: dict, skip_none: bool) -> tuple[str, list, list]:
    """ستون‌های قابل‌نوشتن حاضر در fields را جدا می‌کند."""
    cfg = load_column_config(entity_key)
    table_name = cfg["table"]
    names = []
    values = []
    for name in _writable_names(cfg):
        if name not in fields:
            continue
        value = fields[name]
        if skip_none and value is None:
            continue
        names.append(name)
        values.append(value)
    return table_name, names, values


def _row_to_record(allowed: list, row) -> dict:
    if isinstance(row, dict):
        return {name: json_safe(row[name]) for name in allowed if name in row}
    return {name: json_safe(value) for name, value in zip(allowed, row)}


def _insert_sql(table_name: str, names: list):
    return sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(name) for name in names),
        sql.SQL(", ").join(sql.Placeholder() for _ in names),
        sql.Identifier("id"),
    )


def insert_row_on(connection, entity_key: str, fields: dict) -> int:
    """درج روی اتصال باز؛ برای تراکنش چندمرحله‌ای."""
    table_name, names, values = _collect_writable(entity_key, fields, skip_none=True)
    if not names:
        raise InvalidInputError("هیچ ستون قابل‌نوشتنی برای درج وجود ندارد")
    with connection.cursor() as cursor:
        cursor.execute(_insert_sql(table_name, names), values)
        row = cursor.fetchone()
    if row is None:
        raise InvalidInputError("درج ردیف شناسه‌ای برنگرداند")
    return int(row[0])


def insert_row(entity_key: str, fields: dict) -> int:
    """یک ردیف جدید درج می‌کند و شناسه را برمی‌گرداند."""

    def work(connection):
        return insert_row_on(connection, entity_key, fields)

    return run_query(work, unique_messages_for(entity_key))


def fetch_row(entity_key: str, row_id: int, not_found_error, not_found_message: str):
    """یک ردیف را با شناسه می‌خواند."""
    row = fetch_first(entity_key, {"id": row_id})
    if row is None:
        raise not_found_error(not_found_message)
    return row


def fetch_rows(entity_key: str, limit: int, offset: int) -> list:
    """چند ردیف را با LIMIT و OFFSET و ترتیب YAML می‌خواند."""
    cfg = load_column_config(entity_key)
    table_name = cfg["table"]
    allowed = _allowed_names(cfg)
    order_cols = list(cfg.get("order_by") or ["id"])
    order_dir = str(cfg.get("order_dir") or "ASC").upper()
    if order_dir not in {"ASC", "DESC"}:
        raise InvalidInputError("ترتیب فهرست نامعتبر است")
    order_sql = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(order_dir))
        for name in order_cols
    )
    default_where = dict(cfg.get("list_default_where") or {})
    where_sql = sql.SQL("")
    params = []
    if default_where:
        filterable = set(allowed) | set(_writable_names(cfg)) | {"id"}
        unknown = set(default_where) - filterable
        if unknown:
            raise InvalidInputError("فیلتر پیش‌فرض فهرست نامعتبر است")
        where_sql = sql.SQL(" WHERE {}").format(
            sql.SQL(" AND ").join(
                sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder())
                for name in default_where
            )
        )
        params.extend(default_where.values())
    query = sql.SQL("SELECT {} FROM {} {} ORDER BY {} LIMIT %s OFFSET %s").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in allowed),
        sql.Identifier(table_name),
        where_sql,
        order_sql,
    )
    params.extend([limit, offset])

    def work(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return [_row_to_record(allowed, dict(row)) for row in rows]

    return run_query(work)


def fetch_first_on(
    connection,
    entity_key: str,
    where: dict,
    columns: tuple | None = None,
):
    """اولین ردیف مطابق شرط تساوی را روی اتصال باز می‌خواند یا None."""
    cfg = load_column_config(entity_key)
    table_name = cfg["table"]
    allowed = _allowed_names(cfg)
    select_cols = list(columns) if columns else allowed
    filterable = set(allowed) | set(_writable_names(cfg)) | {"id"}
    unknown = set(where) - filterable
    if unknown:
        raise InvalidInputError("شرط فیلتر نامعتبر است")
    extra = set(select_cols) - set(allowed)
    if extra:
        raise InvalidInputError("ستون خواندن نامعتبر است")
    if not where:
        raise InvalidInputError("شرط خواندن لازم است")
    where_sql = sql.SQL(" AND ").join(
        sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder())
        for name in where
    )
    query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in select_cols),
        sql.Identifier(table_name),
        where_sql,
    )
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, list(where.values()))
        row = cursor.fetchone()
    if row is None:
        return None
    return public_record(dict(row), tuple(select_cols))


def fetch_first(entity_key: str, where: dict, columns: tuple | None = None):
    """اولین ردیف مطابق شرط تساوی را می‌خواند یا None."""

    def work(connection):
        return fetch_first_on(connection, entity_key, where, columns)

    return run_query(work)


def update_row_on(
    connection,
    entity_key: str,
    fields: dict,
    not_found_error,
    not_found_message: str,
) -> int:
    """به‌روزرسانی روی اتصال باز؛ برای تراکنش چندمرحله‌ای."""
    row_id = fields.get("id")
    if not isinstance(row_id, int) or isinstance(row_id, bool) or row_id < 1:
        raise InvalidInputError("شناسه برای به‌روزرسانی نامعتبر است")
    table_name, names, values = _collect_writable(
        entity_key,
        fields,
        skip_none=False,
    )
    if not names:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder())
        for name in names
    )
    query = sql.SQL("UPDATE {} SET {} WHERE {} = {} RETURNING {}").format(
        sql.Identifier(table_name),
        assignments,
        sql.Identifier("id"),
        sql.Placeholder(),
        sql.Identifier("id"),
    )
    with connection.cursor() as cursor:
        cursor.execute(query, values + [row_id])
        row = cursor.fetchone()
    if row is None:
        raise not_found_error(not_found_message)
    return int(row[0])


def update_row(
    entity_key: str,
    fields: dict,
    not_found_error,
    not_found_message: str,
) -> int:
    """یک ردیف موجود را به‌روز می‌کند و شناسه را برمی‌گرداند."""

    def work(connection):
        return update_row_on(
            connection,
            entity_key,
            fields,
            not_found_error,
            not_found_message,
        )

    return run_query(work, unique_messages_for(entity_key))


def delete_row_on(
    connection,
    entity_key: str,
    row_id: int,
    not_found_error,
    not_found_message: str,
) -> int:
    """حذف نرم روی اتصال باز؛ برای تراکنش چندمرحله‌ای."""
    from repository.soft_delete import soft_delete_row_on

    return soft_delete_row_on(
        connection,
        entity_key,
        row_id,
        not_found_error,
        not_found_message,
    )


def delete_row(
    entity_key: str,
    row_id: int,
    not_found_error,
    not_found_message: str,
) -> int:
    """یک ردیف را با شناسه حذف می‌کند."""

    def work(connection):
        return delete_row_on(
            connection,
            entity_key,
            row_id,
            not_found_error,
            not_found_message,
        )

    return run_query(work)


def resolve_lookup_id(entity_key: str, lookup_id, name) -> int:
    """شناسه یک ردیف lookup فعال را از شناسه یا نام برمی‌گرداند."""
    cfg = load_column_config(entity_key)
    if cfg.get("kind") != "lookup":
        raise InvalidInputError("جدول lookup نامعتبر است")
    label = cfg.get("label") or entity_key
    if lookup_id is not None:
        row = fetch_first(entity_key, {"id": lookup_id})
        if row is None:
            raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
    else:
        if not name:
            raise InvalidInputError(f"{label} لازم است")
        row = fetch_first(entity_key, {"name": name})
        if row is None:
            raise InvalidInputError(f"{label} «{name}» پیدا نشد")
    if row.get("is_active") is False:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} غیرفعال است")
        raise InvalidInputError(f"{label} «{name}» غیرفعال است")
    return row["id"]
