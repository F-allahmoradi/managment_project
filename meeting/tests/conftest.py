"""کمک‌های مشترک تست جلسه: مسیر import و ردیف موقت.

درج و حذف روی PostgreSQL واقعی است.
"""

from pathlib import Path
import os
import sys
import uuid

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from services.connection import open_connection
from services.user import insert_user
from services.user_role import insert_user_role


def unique_username(prefix: str = "tmp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def unique_email(prefix: str = "tmp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.test"


def unique_phone() -> str:
    return "09" + uuid.uuid4().hex[:9]


def unique_project_name(prefix: str = "پروژه‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_contact_name(prefix: str = "مخاطب‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_meeting_title(prefix: str = "جلسه‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def insert_temp_user(**overrides) -> int:
    payload = {
        "first_name": "آزمایش",
        "last_name": "جلسه‌موقت",
        "username": unique_username("meet"),
        "password": "secret12",
        "email": unique_email("meet"),
        "is_active": True,
    }
    payload.update(overrides)
    return insert_user(payload)


def _delete_meetings_for_user(cursor, user_id: int) -> None:
    cursor.execute(
        "DELETE FROM meeting_participants WHERE user_id = %s",
        [user_id],
    )
    cursor.execute(
        """
        DELETE FROM meeting_participants
        WHERE meeting_id IN (
            SELECT id FROM meetings
            WHERE manager_user_id = %s
               OR project_id IN (SELECT id FROM projects WHERE created_by = %s)
        )
        """,
        [user_id, user_id],
    )
    cursor.execute(
        """
        DELETE FROM meetings
        WHERE manager_user_id = %s
           OR project_id IN (SELECT id FROM projects WHERE created_by = %s)
        """,
        [user_id, user_id],
    )
    cursor.execute(
        """
        DELETE FROM meeting_schedules
        WHERE user_id = %s
           OR project_id IN (SELECT id FROM projects WHERE created_by = %s)
        """,
        [user_id, user_id],
    )


def delete_temp_user(user_id: int) -> None:
    """ردیف موقت users را بعد از پاک کردن جلسه و پروژه وابسته حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            _delete_meetings_for_user(cursor, user_id)
            cursor.execute(
                """
                DELETE FROM reminders
                WHERE created_by_user_id = %s
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id],
            )
            cursor.execute(
                """
                DELETE FROM chats
                WHERE project_id IN (
                    SELECT id FROM projects WHERE created_by = %s
                )
                """,
                [user_id],
            )
            cursor.execute(
                """
                DELETE FROM task_follow_ups
                WHERE followed_by_user_id = %s
                   OR task_id IN (
                        SELECT id FROM tasks
                        WHERE created_by_user_id = %s
                           OR project_id IN (
                                SELECT id FROM projects WHERE created_by = %s
                           )
                   )
                """,
                [user_id, user_id, user_id],
            )
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE created_by_user_id = %s
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id],
            )
            cursor.execute("DELETE FROM projects WHERE created_by = %s", [user_id])
            cursor.execute(
                "DELETE FROM project_members WHERE user_id = %s",
                [user_id],
            )
            cursor.execute(
                """
                DELETE FROM contents
                WHERE created_by_user_id = %s
                   OR media_file_id IN (
                        SELECT id FROM media_files WHERE uploaded_by_user_id = %s
                   )
                """,
                [user_id, user_id],
            )
            cursor.execute(
                "DELETE FROM media_files WHERE uploaded_by_user_id = %s",
                [user_id],
            )
            cursor.execute("DELETE FROM users WHERE id = %s", [user_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_project(project_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM meeting_participants WHERE meeting_id IN "
                "(SELECT id FROM meetings WHERE project_id = %s)",
                [project_id],
            )
            cursor.execute("DELETE FROM meetings WHERE project_id = %s", [project_id])
            cursor.execute(
                "DELETE FROM meeting_schedules WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM reminders WHERE project_id = %s",
                [project_id],
            )
            cursor.execute("DELETE FROM chats WHERE project_id = %s", [project_id])
            cursor.execute("DELETE FROM tasks WHERE project_id = %s", [project_id])
            cursor.execute("DELETE FROM projects WHERE id = %s", [project_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_meeting(meeting_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM meetings WHERE id = %s", [meeting_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_schedule(schedule_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE meetings SET schedule_id = NULL WHERE schedule_id = %s",
                [schedule_id],
            )
            cursor.execute(
                "DELETE FROM meeting_schedules WHERE id = %s",
                [schedule_id],
            )
        connection.commit()
    finally:
        connection.close()


def delete_temp_external_contact(contact_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM meeting_participants WHERE external_contact_id = %s",
                [contact_id],
            )
            cursor.execute(
                "DELETE FROM external_contacts WHERE id = %s",
                [contact_id],
            )
        connection.commit()
    finally:
        connection.close()


def fetch_seed_role_id(name: str) -> int:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM roles WHERE name = %s", [name])
            row = cursor.fetchone()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError(f"نقش seed {name} در دیتابیس نیست")
    return row[0]


def assign_seed_role(user_id: int, role_name: str) -> int:
    return insert_user_role(
        {"user_id": user_id, "role_id": fetch_seed_role_id(role_name)}
    )


class ActorSession:
    def __init__(self, user_id: int, previous: dict) -> None:
        self.user_id = user_id
        self.previous = previous

    def close(self) -> None:
        _restore_actor_env(self.previous)
        delete_temp_user(self.user_id)


def _snapshot_actor_env() -> dict:
    return {
        "id": os.environ.get("MCP_ACTOR_USER_ID"),
        "username": os.environ.get("MCP_ACTOR_USERNAME"),
    }


def _restore_actor_env(previous: dict) -> None:
    if previous.get("id") is None:
        os.environ.pop("MCP_ACTOR_USER_ID", None)
    else:
        os.environ["MCP_ACTOR_USER_ID"] = previous["id"]
    if previous.get("username") is None:
        os.environ.pop("MCP_ACTOR_USERNAME", None)
    else:
        os.environ["MCP_ACTOR_USERNAME"] = previous["username"]


def bind_actor_as_role(role_name: str) -> ActorSession:
    previous = _snapshot_actor_env()
    user_id = insert_temp_user(last_name="بازیگر-جلسه")
    assign_seed_role(user_id, role_name)
    os.environ["MCP_ACTOR_USER_ID"] = str(user_id)
    os.environ.pop("MCP_ACTOR_USERNAME", None)
    return ActorSession(user_id, previous)
