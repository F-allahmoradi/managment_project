"""کوئری‌های الگو، جلسه، شرکت‌کننده، ضبط و همگام‌سازی.

خروجی sync در tasks و messages ساخته می‌شود؛
این فایل فقط meetings و meeting_sync_items را می‌نویسد.
"""

from datetime import time as dt_time

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from errors.crud import InvalidInputError
from repository.db import fetch_many, fetch_one, json_safe, public_record, run_query

_LOOKUP_TABLES = {
    "meeting_types": "نوع جلسه",
    "meeting_statuses": "وضعیت جلسه",
}

SCHEDULE_COLUMNS = (
    "id",
    "user_id",
    "project_id",
    "meeting_type_id",
    "meeting_type_name",
    "day_of_week",
    "start_time",
    "duration_minutes",
    "is_active",
    "effective_from",
    "effective_until",
    "created_at",
)

MEETING_COLUMNS = (
    "id",
    "project_id",
    "manager_user_id",
    "schedule_id",
    "meeting_type_id",
    "meeting_type_name",
    "status_id",
    "status_name",
    "visibility",
    "title",
    "scheduled_at",
    "scheduled_end_at",
    "duration_minutes",
    "location",
    "held_at",
    "ended_at",
    "content_id",
    "sync_status",
    "synced_at",
    "created_at",
)

PARTICIPANT_COLUMNS = (
    "id",
    "meeting_id",
    "user_id",
    "external_contact_id",
    "role",
    "display_name",
)

SYNC_ITEM_COLUMNS = (
    "id",
    "meeting_id",
    "task_id",
    "message_id",
    "created_by_user_id",
    "created_at",
)

UNIQUE_MESSAGES = {
    "meeting_participants_meeting_user_idx": "این کاربر از قبل در جلسه هست",
    "meeting_participants_meeting_external_idx": "این مخاطب خارجی از قبل در جلسه هست",
}

_SCHEDULE_SELECT = """
SELECT s.id, s.user_id, s.project_id, s.meeting_type_id, t.name AS meeting_type_name,
       s.day_of_week, s.start_time, s.duration_minutes, s.is_active,
       s.effective_from, s.effective_until, s.created_at
FROM meeting_schedules s
JOIN meeting_types t ON t.id = s.meeting_type_id
"""

_MEETING_SELECT = """
SELECT m.id, m.project_id, m.manager_user_id, m.schedule_id,
       m.meeting_type_id, t.name AS meeting_type_name,
       m.status_id, st.name AS status_name,
       m.visibility, m.title, m.scheduled_at, m.scheduled_end_at,
       m.duration_minutes, m.location, m.held_at, m.ended_at,
       m.content_id, m.sync_status, m.synced_at, m.created_at
FROM meetings m
JOIN meeting_types t ON t.id = m.meeting_type_id
JOIN meeting_statuses st ON st.id = m.status_id
"""

_PARTICIPANT_SELECT = """
SELECT p.id, p.meeting_id, p.user_id, p.external_contact_id, p.role,
       COALESCE(
           NULLIF(btrim(concat_ws(' ', u.first_name, u.last_name)), ''),
           u.username,
           c.name
       ) AS display_name
FROM meeting_participants p
LEFT JOIN users u ON u.id = p.user_id
LEFT JOIN external_contacts c ON c.id = p.external_contact_id
"""

_SYNC_ITEM_SELECT = """
SELECT id, meeting_id, task_id, message_id, created_by_user_id, created_at
FROM meeting_sync_items
"""


def _public_with_time(row: dict, columns: tuple) -> dict:
    """time را به رشته تبدیل می‌کند تا JSON بشکند."""
    payload = public_record(row, columns)
    value = payload.get("start_time")
    if isinstance(value, dt_time):
        payload["start_time"] = value.strftime("%H:%M:%S")
    elif value is not None and not isinstance(value, str):
        payload["start_time"] = json_safe(value)
    return payload


def resolve_lookup_id(table: str, lookup_id, name) -> int:
    """شناسه یک ردیف lookup را از شناسه یا نام برمی‌گرداند."""
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
        query = sql.SQL("SELECT * FROM {} WHERE {} = %s LIMIT 1").format(
            sql.Identifier(table),
            sql.Identifier(column),
        )
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, [param])
            found = cursor.fetchone()
        if found is None:
            return None
        return dict(found)

    row = run_query(work)
    if row is None:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
        raise InvalidInputError(f"{label} «{name}» پیدا نشد")
    if row.get("is_active") is False:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} غیرفعال است")
        raise InvalidInputError(f"{label} «{name}» غیرفعال است")
    return int(row["id"])


def fetch_lookup_name(table: str, lookup_id: int) -> str:
    """نام یک ردیف lookup را با شناسه می‌خواند."""
    label = _LOOKUP_TABLES.get(table)
    if label is None:
        raise InvalidInputError("جدول lookup نامعتبر است")

    def work(connection):
        query = sql.SQL("SELECT name FROM {} WHERE id = %s LIMIT 1").format(
            sql.Identifier(table)
        )
        with connection.cursor() as cursor:
            cursor.execute(query, [lookup_id])
            found = cursor.fetchone()
        if found is None:
            return None
        return found[0]

    name = run_query(work)
    if name is None:
        raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
    return name


def fetch_cancelled_status_id() -> int:
    """شناسه وضعیت لغو شده را از seed می‌خواند."""
    return resolve_lookup_id("meeting_statuses", None, "لغو شده")


def fetch_planned_status_id() -> int:
    """شناسه وضعیت برنامه‌ریزی شده را از seed می‌خواند."""
    return resolve_lookup_id("meeting_statuses", None, "برنامه‌ریزی شده")


def fetch_recorded_status_id() -> int:
    """شناسه وضعیت ضبط شده را از seed می‌خواند."""
    return resolve_lookup_id("meeting_statuses", None, "ضبط شده")


def fetch_synced_status_id() -> int:
    """شناسه وضعیت همگام‌سازی شده را از seed می‌خواند."""
    return resolve_lookup_id("meeting_statuses", None, "همگام‌سازی شده")


def fetch_schedule_record(schedule_id: int):
    """یک الگو را با نام نوع می‌خواند یا None."""
    row = fetch_one(
        _SCHEDULE_SELECT + " WHERE s.id = %s",
        [schedule_id],
        SCHEDULE_COLUMNS,
    )
    if row is None:
        return None
    return _public_with_time(row, SCHEDULE_COLUMNS)


def fetch_schedule_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
    is_active=None,
) -> list:
    """فهرست الگوهای یک مدیر را می‌خواند."""
    clauses = ["s.user_id = %s"]
    params = [user_id]
    if project_id is not None:
        clauses.append("s.project_id = %s")
        params.append(project_id)
    if is_active is not None:
        clauses.append("s.is_active = %s")
        params.append(is_active)
    extra = " WHERE " + " AND ".join(clauses)
    params.extend([limit, offset])
    rows = fetch_many(
        _SCHEDULE_SELECT + extra + " ORDER BY s.id DESC LIMIT %s OFFSET %s",
        params,
        SCHEDULE_COLUMNS,
    )
    return [_public_with_time(row, SCHEDULE_COLUMNS) for row in rows]


def fetch_meeting_record(meeting_id: int):
    """یک جلسه را با نام نوع و وضعیت می‌خواند یا None."""
    return fetch_one(
        _MEETING_SELECT + " WHERE m.id = %s",
        [meeting_id],
        MEETING_COLUMNS,
    )


def fetch_meetings_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
    status_id=None,
) -> list:
    """جلساتی را می‌خواند که مدیر، شرکت‌کننده، یا جلسهٔ PROJECT پروژه است."""
    clauses = [
        """
(
    m.manager_user_id = %s
    OR EXISTS (
        SELECT 1 FROM meeting_participants p
        WHERE p.meeting_id = m.id AND p.user_id = %s
    )
    OR (
        m.visibility = 'PROJECT'
        AND m.project_id IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM project_members pm
            WHERE pm.project_id = m.project_id
              AND pm.user_id = %s
              AND pm.is_active = true
        )
    )
)
"""
    ]
    params = [user_id, user_id, user_id]
    if project_id is not None:
        clauses.append("m.project_id = %s")
        params.append(project_id)
    if status_id is not None:
        clauses.append("m.status_id = %s")
        params.append(status_id)
    extra = " WHERE " + " AND ".join(clauses)
    params.extend([limit, offset])
    return fetch_many(
        _MEETING_SELECT
        + extra
        + " ORDER BY m.scheduled_at DESC, m.id DESC LIMIT %s OFFSET %s",
        params,
        MEETING_COLUMNS,
    )


def meeting_has_user_participant(meeting_id: int, user_id: int) -> bool:
    """اگر کاربر در شرکت‌کنندگان جلسه باشد True است."""
    row = fetch_one(
        """
        SELECT id FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        LIMIT 1
        """,
        [meeting_id, user_id],
        ("id",),
    )
    return row is not None


def fetch_participant_records(meeting_id: int) -> list:
    """شرکت‌کنندگان یک جلسه را می‌خواند."""
    return fetch_many(
        _PARTICIPANT_SELECT + " WHERE p.meeting_id = %s ORDER BY p.id ASC",
        [meeting_id],
        PARTICIPANT_COLUMNS,
    )


def fetch_sync_item_records(meeting_id: int) -> list:
    """خروجی‌های همگام‌شدهٔ یک جلسه را می‌خواند."""
    return fetch_many(
        _SYNC_ITEM_SELECT + " WHERE meeting_id = %s ORDER BY id ASC",
        [meeting_id],
        SYNC_ITEM_COLUMNS,
    )


def fetch_overlapping_meeting(
    manager_user_id: int,
    scheduled_at,
    scheduled_end_at,
    cancelled_status_id: int,
    exclude_meeting_id=None,
):
    """اولین جلسهٔ غیرلغو شدهٔ همان مدیر که با بازه تداخل دارد."""
    clauses = [
        "m.manager_user_id = %s",
        "m.status_id <> %s",
        "m.scheduled_at < %s",
        "m.scheduled_end_at > %s",
    ]
    params = [manager_user_id, cancelled_status_id, scheduled_end_at, scheduled_at]
    if exclude_meeting_id is not None:
        clauses.append("m.id <> %s")
        params.append(exclude_meeting_id)
    extra = " WHERE " + " AND ".join(clauses)
    return fetch_one(
        _MEETING_SELECT + extra + " ORDER BY m.scheduled_at ASC LIMIT 1",
        params,
        MEETING_COLUMNS,
    )


def insert_schedule_on(connection, fields: dict) -> int:
    """یک الگوی تکرار درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO meeting_schedules (
                user_id, project_id, meeting_type_id, day_of_week,
                start_time, duration_minutes, is_active,
                effective_from, effective_until
            ) VALUES (
                %(user_id)s, %(project_id)s, %(meeting_type_id)s, %(day_of_week)s,
                %(start_time)s, %(duration_minutes)s, %(is_active)s,
                %(effective_from)s, %(effective_until)s
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def insert_meeting_on(connection, fields: dict) -> int:
    """یک نمونهٔ جلسه درج می‌کند؛ content_id خالی می‌ماند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO meetings (
                project_id, manager_user_id, schedule_id, meeting_type_id,
                status_id, visibility, title, scheduled_at, scheduled_end_at,
                duration_minutes, location, sync_status
            ) VALUES (
                %(project_id)s, %(manager_user_id)s, %(schedule_id)s,
                %(meeting_type_id)s, %(status_id)s, %(visibility)s, %(title)s,
                %(scheduled_at)s, %(scheduled_end_at)s, %(duration_minutes)s,
                %(location)s, 'NOT_SYNCED'
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def cancel_meeting_on(connection, meeting_id: int, cancelled_status_id: int):
    """وضعیت جلسه را به لغو شده می‌برد."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE meetings
            SET status_id = %s
            WHERE id = %s
            RETURNING id
            """,
            [cancelled_status_id, meeting_id],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return int(row[0])


def update_meeting_on(connection, meeting_id: int, fields: dict):
    """عنوان، زمان، مکان، پروژه و نوع جلسه را به‌روز می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE meetings
            SET project_id = %(project_id)s,
                meeting_type_id = %(meeting_type_id)s,
                visibility = %(visibility)s,
                title = %(title)s,
                scheduled_at = %(scheduled_at)s,
                scheduled_end_at = %(scheduled_end_at)s,
                duration_minutes = %(duration_minutes)s,
                location = %(location)s
            WHERE id = %(id)s
            RETURNING id
            """,
            {"id": meeting_id, **fields},
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return int(row[0])


def insert_participant_on(connection, fields: dict) -> int:
    """یک شرکت‌کننده با قانون XOR درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO meeting_participants (
                meeting_id, user_id, external_contact_id, role
            ) VALUES (
                %(meeting_id)s, %(user_id)s, %(external_contact_id)s, %(role)s
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def attach_recording_on(
    connection,
    meeting_id: int,
    content_id: int,
    recorded_status_id: int,
    held_at,
):
    """content_id را وصل می‌کند و وضعیت را به ضبط شده می‌برد."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE meetings
            SET content_id = %s,
                status_id = %s,
                held_at = COALESCE(held_at, %s)
            WHERE id = %s
            RETURNING id
            """,
            [content_id, recorded_status_id, held_at, meeting_id],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return int(row[0])


def mark_meeting_sync_on(
    connection,
    meeting_id: int,
    sync_status: str,
    synced_status_id,
    synced_at,
):
    """sync_status و در صورت موفقیت کامل وضعیت جلسه را به‌روز می‌کند."""
    with connection.cursor() as cursor:
        if sync_status == "SYNCED":
            cursor.execute(
                """
                UPDATE meetings
                SET sync_status = %s,
                    status_id = %s,
                    synced_at = %s
                WHERE id = %s
                RETURNING id
                """,
                [sync_status, synced_status_id, synced_at, meeting_id],
            )
        else:
            cursor.execute(
                """
                UPDATE meetings
                SET sync_status = %s
                WHERE id = %s
                RETURNING id
                """,
                [sync_status, meeting_id],
            )
        row = cursor.fetchone()
    if row is None:
        return None
    return int(row[0])


def insert_sync_item_on(connection, fields: dict) -> int:
    """یک ردیف meeting_sync_items با دقیقاً یک هدف درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO meeting_sync_items (
                meeting_id, task_id, message_id, created_by_user_id
            ) VALUES (
                %(meeting_id)s, %(task_id)s,
                %(message_id)s, %(created_by_user_id)s
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def insert_schedule(fields: dict) -> int:
    """الگو را با run_query درج می‌کند."""

    def work(connection):
        return insert_schedule_on(connection, fields)

    return run_query(work)


def insert_meeting(fields: dict) -> int:
    """جلسه را با run_query درج می‌کند."""

    def work(connection):
        return insert_meeting_on(connection, fields)

    return run_query(work)


def insert_participant(fields: dict) -> int:
    """شرکت‌کننده را با run_query درج می‌کند."""

    def work(connection):
        return insert_participant_on(connection, fields)

    return run_query(work, UNIQUE_MESSAGES)
