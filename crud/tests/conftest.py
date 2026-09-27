"""کمک‌های مشترک تست CRUD: مسیر پروژه و ردیف موقت users.

درج و حذف روی PostgreSQL واقعی است. بعد از هر تست ردیف موقت پاک می‌شود.
"""

from pathlib import Path
import os
import sys
import uuid

_ROOT = Path(__file__).resolve().parent.parent
_REPO = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from services.connection import open_connection
from services.user import insert_user
from services.user_role import insert_user_role


def unique_username(prefix: str = "tmp") -> str:
    """نام کاربری یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def unique_role_name(prefix: str = "نقش‌موقت") -> str:
    """نام نقش یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_permission_pair() -> tuple[str, str]:
    """جفت resource/action یکتا برای مجوز تست می‌سازد."""
    token = uuid.uuid4().hex[:10]
    return f"Tmp{token}", "Ping"


def unique_project_name(prefix: str = "پروژه‌موقت") -> str:
    """نام پروژه یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_task_title(prefix: str = "وظیفه‌موقت") -> str:
    """عنوان وظیفه یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_issue_title(prefix: str = "مسئله‌موقت") -> str:
    """عنوان مسئله یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_task_item_title(prefix: str = "زیرکارموقت") -> str:
    """عنوان زیرکار یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_chat_title(prefix: str = "گفتگوی‌موقت") -> str:
    """عنوان گفتگو یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_contact_name(prefix: str = "مخاطب‌موقت") -> str:
    """نام مخاطب خارجی یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_account_name(prefix: str = "حساب‌موقت") -> str:
    """نام حساب مالی یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def unique_storage_key(prefix: str = "meetings") -> str:
    """کلید ذخیره‌سازی یکتا برای media_files تست می‌سازد."""
    return f"{prefix}/{uuid.uuid4().hex}.ogg"


def unique_email(prefix: str = "tmp") -> str:
    """ایمیل یکتا برای ردیف تست می‌سازد."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.test"


def unique_phone() -> str:
    """شماره تلفن یکتا برای ردیف تست می‌سازد."""
    return "09" + uuid.uuid4().hex[:9]


def minimal_user(**overrides) -> dict:
    """حداقل فیلد معتبر برای ثبت کاربر تست.

    ورودی:
        overrides: جایگزینی فیلدهای پیش‌فرض.
    خروجی:
        دیکشنری آمادهٔ CreateUserInput.
    """
    payload = {
        "first_name": "آزمایش",
        "last_name": "ثبت‌موقت",
        "username": unique_username("create"),
        "password": "secret12",
    }
    payload.update(overrides)
    return payload


def _bypass_task_item_assignee_guard(cursor) -> None:
    """تریگر مسئول زیرکار را برای پاک‌سازی تست خاموش می‌کند."""
    cursor.execute("SET LOCAL app.enforce_task_items_assignee = 'false'")


def insert_temp_user(**overrides) -> int:
    """یک کاربر موقت درج می‌کند و شناسه را برمی‌گرداند.

    ورودی:
        overrides: فیلدهای اضافه یا جایگزین.
    خروجی:
        شناسه ردیف جدید.
    """
    payload = {
        "first_name": "آزمایش",
        "last_name": "خواندن‌موقت",
        "username": unique_username("read"),
        "password": "secret12",
        "email": unique_email("read"),
        "is_active": True,
    }
    payload.update(overrides)
    return insert_user(payload)


def delete_temp_user(user_id: int) -> None:
    """ردیف موقت users را اگر مانده باشد حذف می‌کند.

    پیگیری‌ها و وظایف وابسته و گزارش و ایده/تجربه و پروژه‌هایی
    که همین کاربر ساخته اول پاک می‌شوند تا RESTRICT روی created_by مانع نشود.
    """
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            _bypass_task_item_assignee_guard(cursor)
            cursor.execute(
                """
                DELETE FROM performance_scores
                WHERE user_id = %s
                   OR performance_action_id IN (
                        SELECT id FROM performance_actions
                        WHERE user_id = %s
                           OR created_by_user_id = %s
                           OR project_id IN (
                                SELECT id FROM projects WHERE created_by = %s
                           )
                   )
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id, user_id, user_id, user_id],
            )
            cursor.execute(
                """
                DELETE FROM performance_actions
                WHERE user_id = %s
                   OR created_by_user_id = %s
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id, user_id],
            )
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
                DELETE FROM chats
                WHERE project_id IN (
                    SELECT id FROM projects WHERE created_by = %s
                )
                OR id IN (
                    SELECT chat_id FROM chat_members WHERE user_id = %s
                )
                """,
                [user_id, user_id],
            )
            cursor.execute(
                """
                DELETE FROM issues
                WHERE created_by_user_id = %s
                   OR project_id IN (
                        SELECT id FROM projects WHERE created_by = %s
                   )
                """,
                [user_id, user_id],
            )
            cursor.execute(
                "DELETE FROM text_analyses WHERE created_by_user_id = %s",
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
            cursor.execute(
                "DELETE FROM projects WHERE created_by = %s",
                [user_id],
            )
            cursor.execute(
                "DELETE FROM project_members WHERE user_id = %s",
                [user_id],
            )
            cursor.execute(
                "DELETE FROM notifications WHERE user_id = %s",
                [user_id],
            )
            cursor.execute(
                "DELETE FROM audit_logs WHERE user_id = %s",
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


def delete_temp_role(role_id: int) -> None:
    """ردیف موقت roles را اگر مانده باشد حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM roles WHERE id = %s", [role_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_permission(permission_id: int) -> None:
    """ردیف موقت permissions را اگر مانده باشد حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM permissions WHERE id = %s", [permission_id])
        connection.commit()
    finally:
        connection.close()


def fetch_seed_role_id(name: str) -> int:
    """شناسه یک نقش seed را برمی‌گرداند."""
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


def fetch_seed_permission_id(resource: str, action: str) -> int:
    """شناسه یک مجوز seed را با Resource/Action برمی‌گرداند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM permissions WHERE resource = %s AND action = %s",
                [resource, action],
            )
            row = cursor.fetchone()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError(f"مجوز seed {resource}/{action} در دیتابیس نیست")
    return row[0]


def fetch_seed_lookup_id(table: str, name: str) -> int:
    """شناسه یک ردیف lookup seed را با نام برمی‌گرداند."""
    allowed = {
        "project_types",
        "project_statuses",
        "project_roles",
        "task_statuses",
        "task_priorities",
        "task_importances",
        "follow_up_types",
        "task_follow_up_statuses",
        "chat_types",
        "notification_types",
        "performance_action_types",
        "transaction_types",
        "financial_account_types",
    }
    if table not in allowed:
        raise RuntimeError(f"جدول lookup {table} مجاز نیست")
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id FROM {table} WHERE name = %s", [name])
            row = cursor.fetchone()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError(f"lookup {name} در {table} نیست")
    return row[0]


def delete_temp_project(project_id: int) -> None:
    """ردیف موقت projects را اگر مانده باشد حذف می‌کند.

    وظایف همان پروژه اول پاک می‌شوند چون FK پروژه RESTRICT است.
    پیگیری‌ها با CASCADE از tasks می‌روند. پیام‌ها با CASCADE از چت می‌روند.
    """
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            _bypass_task_item_assignee_guard(cursor)
            cursor.execute(
                """
                DELETE FROM audit_logs
                WHERE (entity = 'Project' AND entity_id = %s)
                   OR (entity = 'Task' AND entity_id IN (
                        SELECT id FROM tasks WHERE project_id = %s
                   ))
                   OR (entity = 'TaskItem' AND entity_id IN (
                        SELECT id FROM task_items
                        WHERE task_id IN (
                            SELECT id FROM tasks WHERE project_id = %s
                        )
                   ))
                   OR (entity = 'ProjectMember' AND entity_id IN (
                        SELECT id FROM project_members WHERE project_id = %s
                   ))
                   OR (entity = 'Issue' AND entity_id IN (
                        SELECT id FROM issues WHERE project_id = %s
                   ))
                   OR (entity = 'PerformanceAction' AND entity_id IN (
                        SELECT id FROM performance_actions WHERE project_id = %s
                   ))
                """,
                [
                    project_id,
                    project_id,
                    project_id,
                    project_id,
                    project_id,
                    project_id,
                ],
            )
            cursor.execute(
                "DELETE FROM performance_scores WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM performance_actions WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM financial_transactions WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM chats WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                """
                DELETE FROM analysis_outputs
                WHERE record_id IN (SELECT id FROM tasks WHERE project_id = %s)
                  AND output_type_id = (
                    SELECT id FROM analysis_output_types WHERE code = 'task'
                  )
                """,
                [project_id],
            )
            cursor.execute(
                """
                DELETE FROM issue_causes
                WHERE issue_id IN (SELECT id FROM issues WHERE project_id = %s)
                   OR cause_issue_id IN (SELECT id FROM issues WHERE project_id = %s)
                """,
                [project_id, project_id],
            )
            cursor.execute(
                "DELETE FROM issues WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM text_analyses WHERE project_id = %s",
                [project_id],
            )
            cursor.execute(
                "DELETE FROM tasks WHERE project_id = %s",
                [project_id],
            )
            cursor.execute("DELETE FROM projects WHERE id = %s", [project_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_task(task_id: int) -> None:
    """ردیف موقت tasks را اگر مانده باشد حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            _bypass_task_item_assignee_guard(cursor)
            cursor.execute(
                """
                DELETE FROM audit_logs
                WHERE (entity = 'Task' AND entity_id = %s)
                   OR (entity = 'TaskItem' AND entity_id IN (
                        SELECT id FROM task_items WHERE task_id = %s
                   ))
                """,
                [task_id, task_id],
            )
            cursor.execute(
                """
                DELETE FROM analysis_outputs
                WHERE record_id = %s
                  AND output_type_id = (
                    SELECT id FROM analysis_output_types WHERE code = 'task'
                  )
                """,
                [task_id],
            )
            cursor.execute("DELETE FROM tasks WHERE id = %s", [task_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_issue(issue_id: int) -> None:
    """ردیف موقت issues را اگر مانده باشد حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM issue_causes
                WHERE issue_id = %s OR cause_issue_id = %s
                """,
                [issue_id, issue_id],
            )
            cursor.execute(
                "DELETE FROM audit_logs WHERE entity = 'Issue' AND entity_id = %s",
                [issue_id],
            )
            cursor.execute("DELETE FROM issues WHERE id = %s", [issue_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_chat(chat_id: int) -> None:
    """ردیف موقت chats را اگر مانده باشد حذف می‌کند.

    پیام‌ها و اعضا و گیرنده‌ها با CASCADE می‌روند.
    """
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM chats WHERE id = %s", [chat_id])
        connection.commit()
    finally:
        connection.close()


def delete_temp_external_contact(contact_id: int) -> None:
    """ردیف موقت external_contacts را اگر مانده باشد حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM external_contacts WHERE id = %s",
                [contact_id],
            )
        connection.commit()
    finally:
        connection.close()


def insert_temp_account(name=None) -> int:
    """یک حساب موقت با نوع seed حساب سازمان می‌سازد."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO financial_accounts (name, account_type_id, balance, is_active)
                SELECT %s, id, 0, true
                FROM financial_account_types
                WHERE name = 'حساب سازمان'
                RETURNING id
                """,
                [name or unique_account_name()],
            )
            row = cursor.fetchone()
        connection.commit()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError("ساخت حساب موقت ناموفق بود")
    return row[0]


def delete_temp_account(account_id: int) -> None:
    """حساب موقت و تراکنش‌های همان حساب را حذف می‌کند."""
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE performance_actions
                SET financial_transaction_id = NULL
                WHERE financial_transaction_id IN (
                    SELECT id FROM financial_transactions WHERE account_id = %s
                )
                """,
                [account_id],
            )
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


def assign_seed_role(user_id: int, role_name: str) -> int:
    """یک نقش seed را به کاربر تست می‌دهد."""
    return insert_user_role(
        {"user_id": user_id, "role_id": fetch_seed_role_id(role_name)}
    )


class ActorSession:
    """بازیگر موقت MCP را نگه می‌دارد و در پایان پاک می‌کند."""

    def __init__(self, user_id: int, previous: dict) -> None:
        self.user_id = user_id
        self.previous = previous

    def close(self) -> None:
        """متغیر محیط را برمی‌گرداند و کاربر موقت را حذف می‌کند."""
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
    """کاربر موقت با نقش seed می‌سازد و او را بازیگر جاری می‌کند."""
    previous = _snapshot_actor_env()
    user_id = insert_temp_user(last_name="بازیگر-دسترسی")
    assign_seed_role(user_id, role_name)
    os.environ["MCP_ACTOR_USER_ID"] = str(user_id)
    os.environ.pop("MCP_ACTOR_USERNAME", None)
    return ActorSession(user_id, previous)


class AuthorizedActorMixin:
    """تست ابزار User را با بازیگر مدیر کل اجرا می‌کند."""

    def setUp(self) -> None:
        self._actor = bind_actor_as_role("مدیر کل")

    def tearDown(self) -> None:
        self._actor.close()

