"""کوئری‌های تعریف یادآوری، پیگیری گیرنده، و لاگ ارسال."""

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from errors.crud import InvalidInputError, ReminderNotFoundError
from repository.db import fetch_many, fetch_one, public_record, run_query

_LOOKUP_TABLES = {
    "reminder_types": "نوع یادآوری",
    "reminder_frequencies": "تکرار یادآوری",
    "reminder_statuses": "وضعیت یادآوری",
    "follow_up_state_statuses": "وضعیت پیگیری گیرنده",
}

REMINDER_COLUMNS = (
    "id",
    "project_id",
    "created_by_user_id",
    "reminder_type_id",
    "reminder_type_name",
    "frequency_id",
    "frequency_name",
    "title",
    "message_template",
    "scheduled_at",
    "next_run_at",
    "last_run_at",
    "status_id",
    "status_name",
    "created_at",
)

_REMINDER_SELECT = """
SELECT r.id, r.project_id, r.created_by_user_id,
       r.reminder_type_id, rt.name AS reminder_type_name,
       r.frequency_id, rf.name AS frequency_name,
       r.title, r.message_template,
       r.scheduled_at, r.next_run_at, r.last_run_at,
       r.status_id, rs.name AS status_name, r.created_at
FROM reminders r
JOIN reminder_types rt ON rt.id = r.reminder_type_id
JOIN reminder_frequencies rf ON rf.id = r.frequency_id
JOIN reminder_statuses rs ON rs.id = r.status_id
"""

FOLLOW_UP_COLUMNS = (
    "id",
    "reminder_id",
    "user_id",
    "external_contact_id",
    "attempt_count",
    "last_sent_at",
    "responded_at",
    "response_text",
    "status_id",
    "status_name",
)

_FOLLOW_UP_SELECT = """
SELECT f.id, f.reminder_id, f.user_id, f.external_contact_id,
       f.attempt_count, f.last_sent_at, f.responded_at, f.response_text,
       f.status_id, fs.name AS status_name
FROM follow_up_states f
JOIN follow_up_state_statuses fs ON fs.id = f.status_id
"""

UNIQUE_MESSAGES = {
    "reminder_targets_reminder_user_idx": (
        "این کاربر از قبل گیرندهٔ همین یادآوری است"
    ),
    "reminder_targets_reminder_external_idx": (
        "این مخاطب خارجی از قبل گیرندهٔ همین یادآوری است"
    ),
    "follow_up_states_reminder_user_idx": (
        "وضعیت پیگیری این کاربر از قبل هست"
    ),
    "follow_up_states_reminder_external_idx": (
        "وضعیت پیگیری این مخاطب خارجی از قبل هست"
    ),
    "execution_logs_idempotency_key_key": (
        "ارسال با این کلید idempotency قبلاً ثبت شده است"
    ),
}

EXECUTION_LOG_COLUMNS = (
    "id",
    "reminder_id",
    "user_id",
    "external_contact_id",
    "channel",
    "rendered_message",
    "status",
    "attempt_number",
    "scheduled_for",
    "sent_at",
    "error_message",
    "idempotency_key",
    "created_at",
)

_EXECUTION_LOG_SELECT = """
SELECT el.id, el.reminder_id, el.user_id, el.external_contact_id,
       el.channel, el.rendered_message, el.status, el.attempt_number,
       el.scheduled_for, el.sent_at, el.error_message,
       el.idempotency_key, el.created_at
FROM execution_logs el
"""


def resolve_lookup_id(table: str, lookup_id, name) -> int:
    """شناسه یک ردیف lookup فعال را از شناسه یا نام برمی‌گرداند."""
    label = _LOOKUP_TABLES.get(table)
    if label is None:
        raise InvalidInputError("جدول lookup نامعتبر است")
    if lookup_id is not None:
        column = "id"
        param = lookup_id
    else:
        if not name:
            raise InvalidInputError(f"{label} لازم است")
        column = "name"
        param = name

    def work(connection):
        query = sql.SQL(
            "SELECT id, name, is_active FROM {} WHERE {} = %s LIMIT 1"
        ).format(sql.Identifier(table), sql.Identifier(column))
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, [param])
            found = cursor.fetchone()
        if found is None:
            return None
        return public_record(dict(found), ("id", "name", "is_active"))

    row = run_query(work)
    if row is None:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
        raise InvalidInputError(f"{label} «{name}» پیدا نشد")
    if row.get("is_active") is False:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} غیرفعال است")
        raise InvalidInputError(f"{label} «{name}» غیرفعال است")
    return row["id"]


def fetch_reminder_record(reminder_id: int):
    """یک یادآوری را با نام lookupها می‌خواند یا None."""
    return fetch_one(
        _REMINDER_SELECT + " WHERE r.id = %s",
        [reminder_id],
        REMINDER_COLUMNS,
    )


def reminder_targets_user(reminder_id: int, user_id: int) -> bool:
    """اگر کاربر گیرندهٔ همین یادآوری باشد True است."""
    row = fetch_one(
        """
        SELECT id FROM reminder_targets
        WHERE reminder_id = %s AND user_id = %s
        LIMIT 1
        """,
        [reminder_id, user_id],
        ("id",),
    )
    return row is not None


def fetch_reminders_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """یادآوری‌هایی را می‌خواند که سازنده، گیرنده، یا عضو پروژه است."""
    params = [user_id, user_id, user_id]
    extra = ""
    if project_id is not None:
        extra = " AND r.project_id = %s"
        params.append(project_id)
    params.extend([limit, offset])
    query = (
        _REMINDER_SELECT
        + """
WHERE (
    r.created_by_user_id = %s
    OR EXISTS (
        SELECT 1 FROM reminder_targets t
        WHERE t.reminder_id = r.id AND t.user_id = %s
    )
    OR EXISTS (
        SELECT 1 FROM project_members pm
        WHERE pm.project_id = r.project_id
          AND pm.user_id = %s
          AND pm.is_active = true
    )
)
"""
        + extra
        + " ORDER BY r.id DESC LIMIT %s OFFSET %s"
    )
    return fetch_many(query, params, REMINDER_COLUMNS)


def fetch_follow_up_state_records(
    reminder_id: int,
    limit: int,
    offset: int,
) -> list:
    """وضعیت پیگیری گیرنده‌های یک یادآوری را می‌خواند."""
    return fetch_many(
        _FOLLOW_UP_SELECT
        + " WHERE f.reminder_id = %s ORDER BY f.id ASC LIMIT %s OFFSET %s",
        [reminder_id, limit, offset],
        FOLLOW_UP_COLUMNS,
    )


def count_execution_logs(reminder_id: int) -> int:
    """تعداد ردیف execution_logs همین یادآوری را برمی‌گرداند."""
    row = fetch_one(
        "SELECT COUNT(*) AS n FROM execution_logs WHERE reminder_id = %s",
        [reminder_id],
        ("n",),
    )
    return int(row["n"]) if row else 0


def fetch_execution_log_records(
    reminder_id: int,
    limit: int,
    offset: int,
) -> list:
    """لاگ ارسال یک یادآوری را به ترتیب زمان می‌خواند."""
    return fetch_many(
        _EXECUTION_LOG_SELECT
        + " WHERE el.reminder_id = %s ORDER BY el.id ASC LIMIT %s OFFSET %s",
        [reminder_id, limit, offset],
        EXECUTION_LOG_COLUMNS,
    )


def lock_reminder_on(connection, reminder_id: int) -> None:
    """یادآوری را برای ارسال سری قفل می‌کند تا کلید idempotency دوبل نشود."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM reminders WHERE id = %s FOR UPDATE",
            [reminder_id],
        )
        row = cursor.fetchone()
    if row is None:
        raise ReminderNotFoundError(
            f"یادآوری با شناسه {reminder_id} پیدا نشد"
        )


def fetch_follow_up_state_records_on(connection, reminder_id: int) -> list:
    """وضعیت پیگیری گیرنده‌ها را روی اتصال باز می‌خواند."""
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            _FOLLOW_UP_SELECT + " WHERE f.reminder_id = %s ORDER BY f.id ASC",
            [reminder_id],
        )
        rows = cursor.fetchall()
    return [public_record(dict(row), FOLLOW_UP_COLUMNS) for row in rows]


def fetch_execution_log_by_key_on(connection, idempotency_key: str):
    """یک لاگ را با کلید idempotency روی اتصال باز می‌خواند یا None."""
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            _EXECUTION_LOG_SELECT + " WHERE el.idempotency_key = %s LIMIT 1",
            [idempotency_key],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return public_record(dict(row), EXECUTION_LOG_COLUMNS)


def max_attempt_number_on(
    connection,
    reminder_id: int,
    user_id,
    external_contact_id,
    channel: str,
) -> int:
    """بزرگ‌ترین شماره تلاش همین گیرنده و کانال را برمی‌گرداند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(attempt_number), 0)
            FROM execution_logs
            WHERE reminder_id = %s
              AND channel = %s
              AND (
                    (user_id IS NOT NULL AND user_id = %s)
                 OR (external_contact_id IS NOT NULL
                     AND external_contact_id = %s)
              )
            """,
            [reminder_id, channel, user_id, external_contact_id],
        )
        row = cursor.fetchone()
    return int(row[0]) if row else 0


def insert_execution_log_on(connection, fields: dict) -> dict:
    """یک ردیف execution_logs را روی اتصال باز درج می‌کند و می‌خواند."""
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO execution_logs (
                reminder_id, user_id, external_contact_id, channel,
                rendered_message, status, attempt_number, scheduled_for,
                sent_at, error_message, idempotency_key
            ) VALUES (
                %(reminder_id)s, %(user_id)s, %(external_contact_id)s,
                %(channel)s, %(rendered_message)s, %(status)s,
                %(attempt_number)s, %(scheduled_for)s, %(sent_at)s,
                %(error_message)s, %(idempotency_key)s
            )
            RETURNING id, reminder_id, user_id, external_contact_id,
                      channel, rendered_message, status, attempt_number,
                      scheduled_for, sent_at, error_message,
                      idempotency_key, created_at
            """,
            fields,
        )
        row = cursor.fetchone()
    return public_record(dict(row), EXECUTION_LOG_COLUMNS)


def mark_follow_up_sent_on(connection, state_id: int) -> None:
    """بعد از ارسال موفق، شمار تلاش و زمان آخرین ارسال را به‌روز می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE follow_up_states
            SET attempt_count = attempt_count + 1,
                last_sent_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            [state_id],
        )


def mark_reminder_ran_on(connection, reminder_id: int) -> None:
    """زمان آخرین اجرای یادآوری را بعد از ارسال می‌نویسد."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE reminders
            SET last_run_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            [reminder_id],
        )


def insert_reminder_graph_on(
    connection,
    reminder_fields: dict,
    targets: list,
    pending_status_id: int,
) -> int:
    """یادآوری، گیرنده‌ها و follow_up_states را در یک تراکنش درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO reminders (
                project_id, created_by_user_id, reminder_type_id, frequency_id,
                title, message_template, scheduled_at, next_run_at, status_id
            ) VALUES (
                %(project_id)s, %(created_by_user_id)s, %(reminder_type_id)s,
                %(frequency_id)s, %(title)s, %(message_template)s,
                %(scheduled_at)s, %(next_run_at)s, %(status_id)s
            )
            RETURNING id
            """,
            reminder_fields,
        )
        row = cursor.fetchone()
        reminder_id = int(row[0])
        for target in targets:
            cursor.execute(
                """
                INSERT INTO reminder_targets (reminder_id, user_id, external_contact_id)
                VALUES (%s, %s, %s)
                """,
                [reminder_id, target["user_id"], target["external_contact_id"]],
            )
            cursor.execute(
                """
                INSERT INTO follow_up_states (
                    reminder_id, user_id, external_contact_id,
                    attempt_count, status_id
                ) VALUES (%s, %s, %s, 0, %s)
                """,
                [
                    reminder_id,
                    target["user_id"],
                    target["external_contact_id"],
                    pending_status_id,
                ],
            )
    return reminder_id


def update_reminder_row(fields: dict) -> int:
    """ستون‌های تعریف یادآوری را به‌روز می‌کند؛ گیرنده دست نمی‌خورد."""
    reminder_id = fields["id"]
    assignments = []
    values = []
    for name in (
        "title",
        "message_template",
        "scheduled_at",
        "next_run_at",
        "reminder_type_id",
        "frequency_id",
        "status_id",
    ):
        if name in fields:
            assignments.append(
                sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder())
            )
            values.append(fields[name])
    if not assignments:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    query = sql.SQL("UPDATE reminders SET {} WHERE id = %s RETURNING id").format(
        sql.SQL(", ").join(assignments)
    )
    values.append(reminder_id)

    def work(connection):
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            row = cursor.fetchone()
        if row is None:
            raise ReminderNotFoundError(
                f"یادآوری با شناسه {reminder_id} پیدا نشد"
            )
        return int(row[0])

    return run_query(work)


def insert_reminder_graph(reminder_fields: dict, targets: list, pending_status_id: int) -> int:
    """گراف تعریف یادآوری را با run_query درج می‌کند."""

    def work(connection):
        return insert_reminder_graph_on(
            connection,
            reminder_fields,
            targets,
            pending_status_id,
        )

    return run_query(work, UNIQUE_MESSAGES)
