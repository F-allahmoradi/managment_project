"""کمک‌های مشترک تست مالی: مسیر import و ردیف موقت.

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


def unique_project_name(prefix: str = "پروژه‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_account_name(prefix: str = "حساب‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_category_name(prefix: str = "دسته‌موقت") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def insert_temp_user(**overrides) -> int:
    payload = {
        "first_name": "آزمایش",
        "last_name": "مالی‌موقت",
        "username": unique_username("finance"),
        "password": "secret12",
        "email": unique_email("finance"),
        "is_active": True,
    }
    payload.update(overrides)
    return insert_user(payload)


def delete_temp_user(user_id: int) -> None:
    """ردیف موقت users را بعد از پاک کردن حساب و تراکنش وابسته حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM financial_transactions
                WHERE user_id = %s
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id],
            )
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
            cursor.execute("DELETE FROM users WHERE id = %s", [user_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_project(project_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM financial_transactions WHERE project_id = %s",
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


def delete_temp_account(account_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM financial_transactions WHERE account_id = %s",
                [account_id],
            )
            cursor.execute(
                "DELETE FROM financial_accounts WHERE id = %s",
                [account_id],
            )
        connection.commit()
    finally:
        connection.close()


def delete_temp_category(category_id: int) -> None:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE financial_transactions SET category_id = NULL WHERE category_id = %s",
                [category_id],
            )
            cursor.execute(
                "DELETE FROM financial_categories WHERE id = %s",
                [category_id],
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
    user_id = insert_temp_user(last_name="بازیگر-مالی")
    assign_seed_role(user_id, role_name)
    os.environ["MCP_ACTOR_USER_ID"] = str(user_id)
    os.environ.pop("MCP_ACTOR_USERNAME", None)
    return ActorSession(user_id, previous)
