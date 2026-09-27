"""اجرای یک‌بارهٔ اتصال، ترجمهٔ خطا، و تبدیل مقدار برای JSON.

سرویس دامنه این توابع را مستقیم صدا نمی‌زند؛ موتور repository صدا می‌زند.
"""

from datetime import date, datetime
from decimal import Decimal

from psycopg2 import Error as PsycopgError
from psycopg2.errors import (
    CheckViolation,
    ForeignKeyViolation,
    QueryCanceled,
    RaiseException,
    UniqueViolation,
)
from psycopg2.extras import RealDictCursor

from errors.crud import (
    DatabaseError,
    InvalidInputError,
    PermissionDeniedError,
    QueryTimeoutError,
)
from repository.connection import open_connection

_TASK_ITEM_ASSIGNEE_MARKERS = (
    "Only task assignee",
    "Task has no assignee",
    "app.current_user_id must be set",
    "created_by_user_id must equal task assignee",
    "completed_by_user_id must equal task assignee",
)


def json_safe(value):
    """مقدار PostgreSQL را برای JSON پاسخ MCP آماده می‌کند."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def as_date(value):
    """تاریخ پاسخ JSON یا ورودی Pydantic را به date تبدیل می‌کند."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def public_record(row: dict, columns: tuple) -> dict:
    """فقط ستون‌های اعلام‌شده را JSON-safe برمی‌گرداند."""
    return {name: json_safe(row[name]) for name in columns if name in row}


def _pg_primary(exc: PsycopgError) -> str:
    """پیام اصلی PostgreSQL را بدون جزئیات اتصال برمی‌گرداند."""
    if exc.diag is not None and exc.diag.message_primary:
        return exc.diag.message_primary
    return str(exc).split("\n", 1)[0]


def set_current_user_id_on(connection, user_id: int) -> None:
    """هویت کاربر جاری را روی تراکنش جاری می‌گذارد (SET LOCAL)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_user_id', %s, true)",
            [str(user_id)],
        )


def disable_task_item_assignee_guard_on(connection) -> None:
    """قید مسئول زیرکار را روی همین تراکنش خاموش می‌کند.

    حذف خود وظیفه باید CASCADE زیرکارها را رد کند؛ آن قید برای
    ویرایش مستقیم task_items است نه برای Task/Delete.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.enforce_task_items_assignee', 'false', true)"
        )


def translate_db_error(exc: PsycopgError, unique_messages: dict | None = None) -> None:
    """خطای psycopg2 را به خطای معنایی CRUD تبدیل می‌کند و پرتاب می‌کند."""
    unique_messages = unique_messages or {}
    if isinstance(exc, QueryCanceled):
        raise QueryTimeoutError("زمان اجرای کوئری از ۱۰ ثانیه بیشتر شد") from exc
    if isinstance(exc, UniqueViolation):
        constraint = ""
        if exc.diag is not None:
            constraint = exc.diag.constraint_name or ""
        message = unique_messages.get(constraint, "مقدار تکراری است")
        raise InvalidInputError(message) from exc
    if isinstance(exc, CheckViolation):
        constraint = ""
        if exc.diag is not None:
            constraint = exc.diag.constraint_name or ""
        message = unique_messages.get(constraint, "مقدار با قید جدول سازگار نیست")
        raise InvalidInputError(message) from exc
    if isinstance(exc, ForeignKeyViolation):
        constraint = ""
        if exc.diag is not None:
            constraint = exc.diag.constraint_name or ""
        mapped = unique_messages.get(constraint)
        if mapped:
            raise InvalidInputError(mapped) from exc
        primary = _pg_primary(exc).lower()
        if "still referenced" in primary or "update or delete on table" in primary:
            raise InvalidInputError("این ردیف وابسته دارد و حذف نمی‌شود") from exc
        raise InvalidInputError("ارجاع به ردیف ناموجود است") from exc
    if isinstance(exc, RaiseException):
        primary = _pg_primary(exc)
        if any(marker in primary for marker in _TASK_ITEM_ASSIGNEE_MARKERS):
            raise PermissionDeniedError(
                "فقط مسئول همین وظیفه می‌تواند زیرکار را تغییر دهد"
            ) from exc
        if "parent_item_id must belong to the same task" in primary:
            raise InvalidInputError("زیرکار والد باید مال همین وظیفه باشد") from exc
        if "task_id cannot be changed" in primary:
            raise InvalidInputError("شناسه وظیفه زیرکار عوض نمی‌شود") from exc
        if "created_by_user_id cannot be changed" in primary:
            raise InvalidInputError("سازنده زیرکار عوض نمی‌شود") from exc
        if "private chat must not have a task" in primary:
            raise InvalidInputError("گفتگوی خصوصی نباید به وظیفه وصل باشد") from exc
        if "task must belong to the same project as the chat" in primary:
            raise InvalidInputError("تسک باید در همان پروژهٔ گفتگو باشد") from exc
        if "sender must be an active project member" in primary:
            raise InvalidInputError("فرستنده باید عضو فعال همین پروژه باشد") from exc
        if "sender must be a chat member" in primary:
            raise InvalidInputError("فرستنده باید عضو همین گفتگو باشد") from exc
        raise InvalidInputError("تغییر زیرکار مجاز نیست") from exc
    raise DatabaseError("اجرای کوئری در PostgreSQL ناموفق بود") from exc


def run_query(work, unique_messages: dict | None = None):
    """اتصال کوتاه‌عمر باز می‌کند، work را اجرا می‌کند و commit می‌کند."""
    connection = open_connection()
    try:
        try:
            result = work(connection)
            connection.commit()
            return result
        except PsycopgError as exc:
            connection.rollback()
            translate_db_error(exc, unique_messages)
    finally:
        connection.close()


def fetch_one(sql: str, params, columns: tuple):
    """یک ردیف را با ستون‌های مشخص می‌خواند یا None."""

    def work(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        if row is None:
            return None
        return public_record(dict(row), columns)

    return run_query(work)


def fetch_many(sql: str, params, columns: tuple) -> list:
    """چند ردیف را با ستون‌های مشخص می‌خواند."""

    def work(connection):
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [public_record(dict(row), columns) for row in rows]

    return run_query(work)
