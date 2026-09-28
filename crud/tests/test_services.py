"""تست اتصال PostgreSQL و سرویس users روی دیتابیس واقعی.

ردیف موقت ساخته می‌شود و در finally پاک می‌شود تا دادهٔ پایدار نماند.
"""

from pathlib import Path
import os
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
_REPO = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from auth.hash_password import verify_password
from errors.crud import (
    INVALID_INPUT,
    PERMISSION_DENIED,
    PROJECT_NOT_FOUND,
    TASK_NOT_FOUND,
    USER_NOT_FOUND,
    CONTENT_NOT_FOUND,
    InvalidInputError,
    PermissionDeniedError,
    ProjectNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
)
from middleware.query_timeout import load_timeout_ms
from repository import fetch_row
from schemas.crud.user import CreateUserInput
from services.connection import load_database_config, open_connection
from services.user import (
    delete_user,
    fetch_user,
    fetch_users,
    insert_user,
    update_user,
)
from services.permission import fetch_permissions, insert_permission
from services.project import (
    delete_project,
    fetch_project,
    fetch_projects_for_actor,
    insert_project,
)
from services.project_member import fetch_project_members, insert_project_member
from services.task import (
    delete_task,
    fetch_task,
    fetch_tasks_for_actor,
    insert_task,
    update_task,
)
from services.task_item import (
    complete_task_item,
    delete_task_item,
    fetch_task_items,
    insert_task_item,
)
from services.task_follow_up import (
    count_task_follow_ups,
    fetch_task_follow_ups,
    insert_task_follow_up,
)
from services.external_contact import fetch_external_contact, insert_external_contact
from services.chat import fetch_chat, fetch_chats_for_actor, insert_chat
from services.chat_member import fetch_chat_members, insert_chat_member
from services.message import fetch_message, fetch_messages_for_actor, insert_message
from services.message_recipient import fetch_message_recipients, insert_message_recipient
from services.performance_action import (
    insert_performance_action,
    score_totals_for_user,
)
from services.content import fetch_content, insert_content
from services.role import delete_role, fetch_role, fetch_roles, insert_role, update_role
from services.role_permission import insert_role_permission
from services.user_role import insert_user_role
from tests.conftest import (
    delete_temp_permission,
    delete_temp_project,
    delete_temp_role,
    delete_temp_user,
    delete_temp_chat,
    delete_temp_external_contact,
    fetch_seed_role_id,
    insert_temp_user,
    minimal_user,
    unique_email,
    unique_phone,
    unique_permission_pair,
    unique_project_name,
    unique_role_name,
    unique_task_title,
    unique_task_item_title,
    unique_chat_title,
    unique_contact_name,
    unique_username,
    unique_account_name,
    insert_temp_account,
    delete_temp_account,
    unique_storage_key,
)


class ConnectionTests(unittest.TestCase):
    """YAML اتصال و کوئری ساده روی Postgres واقعی را بررسی می‌کند."""

    def test_yaml_points_at_management_postgres(self) -> None:
        source = load_database_config()
        self.assertEqual(source["type"], "postgresql")
        expected_host = (os.environ.get("POSTGRES_HOST") or "127.0.0.1").strip()
        expected_port = int((os.environ.get("POSTGRES_PORT") or "5437").strip())
        self.assertEqual(source["host"], expected_host)
        self.assertEqual(int(source["port"]), expected_port)
        self.assertEqual(source["database"], os.environ.get("POSTGRES_DB") or "management_db")
        self.assertEqual(source["user"], os.environ.get("POSTGRES_USER") or "management")
        self.assertEqual(source["users_table"], "users")

    def test_postgres_env_overrides_yaml_host(self) -> None:
        previous = os.environ.get("POSTGRES_HOST")
        os.environ["POSTGRES_HOST"] = "postgres"
        try:
            source = load_database_config()
            self.assertEqual(source["host"], "postgres")
        finally:
            if previous is None:
                os.environ.pop("POSTGRES_HOST", None)
            else:
                os.environ["POSTGRES_HOST"] = previous

    def test_timeout_is_ten_seconds(self) -> None:
        self.assertEqual(load_timeout_ms(), 10_000)

    def test_open_connection_selects_one(self) -> None:
        connection = open_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            connection.close()

    def test_users_table_exists(self) -> None:
        connection = open_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'users'
                    """
                )
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            connection.close()


class UserServiceTests(unittest.TestCase):
    """INSERT/SELECT/UPDATE/DELETE روی جدول users را بررسی می‌کند."""

    def test_insert_hashes_password_and_cleans_up(self) -> None:
        parsed = CreateUserInput(**minimal_user(password="secret12"))
        new_id = insert_user(parsed.model_dump())
        try:
            self.assertIsInstance(new_id, int)
            self.assertGreater(new_id, 0)
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT first_name, username, password_hash, is_active "
                        "FROM users WHERE id = %s",
                        [new_id],
                    )
                    row = cursor.fetchone()
            finally:
                connection.close()
            self.assertEqual(row[0], "آزمایش")
            self.assertEqual(row[1], parsed.username)
            self.assertNotEqual(row[2], "secret12")
            self.assertTrue(str(row[2]).startswith("pbkdf2_sha256$"))
            self.assertTrue(verify_password("secret12", row[2]))
            self.assertTrue(row[3])
        finally:
            delete_temp_user(new_id)

    def test_fetch_returns_public_columns_without_password_hash(self) -> None:
        new_id = insert_temp_user()
        try:
            user = fetch_user(new_id)
            self.assertEqual(user["id"], new_id)
            self.assertEqual(user["first_name"], "آزمایش")
            self.assertEqual(user["last_name"], "خواندن‌موقت")
            self.assertTrue(user["is_active"])
            self.assertNotIn("password", user)
            self.assertNotIn("password_hash", user)
            self.assertEqual(
                set(user),
                {
                    "id",
                    "first_name",
                    "last_name",
                    "phone",
                    "email",
                    "username",
                    "is_active",
                    "created_at",
                },
            )
        finally:
            delete_temp_user(new_id)

    def test_fetch_missing_id_raises_user_not_found(self) -> None:
        new_id = insert_temp_user()
        delete_temp_user(new_id)
        with self.assertRaises(UserNotFoundError) as caught:
            fetch_user(new_id)
        self.assertEqual(caught.exception.error_code, USER_NOT_FOUND)

    def test_list_includes_new_row_without_password_hash(self) -> None:
        new_id = insert_temp_user(last_name="فهرست‌موقت")
        try:
            records = fetch_users(limit=50, offset=0)
            self.assertGreaterEqual(len(records), 1)
            self.assertLessEqual(len(records), 50)
            fetched_ids = {row["id"] for row in records}
            self.assertIn(new_id, fetched_ids)
            for row in records:
                self.assertNotIn("password", row)
                self.assertNotIn("password_hash", row)
                self.assertIn("username", row)
        finally:
            delete_temp_user(new_id)

    def test_duplicate_username_is_invalid_input(self) -> None:
        username = unique_username("dup")
        first_id = insert_temp_user(username=username)
        try:
            with self.assertRaises(InvalidInputError) as caught:
                insert_user(minimal_user(username=username))
            self.assertEqual(caught.exception.error_code, INVALID_INPUT)
            self.assertIn("نام کاربری", caught.exception.message)
        finally:
            delete_temp_user(first_id)

    def test_update_changes_only_given_fields_then_cleanup(self) -> None:
        new_id = insert_temp_user()
        try:
            updated_id = update_user(
                {"id": new_id, "last_name": "ویرایش‌موقت", "is_active": False}
            )
            self.assertEqual(updated_id, new_id)
            row = fetch_row(
                "users",
                new_id,
                UserNotFoundError,
                f"کاربر با شناسه {new_id} پیدا نشد",
            )
            self.assertEqual(row["last_name"], "ویرایش‌موقت")
            self.assertFalse(row["is_active"])
            self.assertEqual(row["first_name"], "آزمایش")
            with self.assertRaises(UserNotFoundError):
                fetch_user(new_id)
        finally:
            delete_temp_user(new_id)

    def test_update_missing_id_raises_user_not_found(self) -> None:
        new_id = insert_temp_user()
        delete_temp_user(new_id)
        with self.assertRaises(UserNotFoundError) as caught:
            update_user({"id": new_id, "last_name": "نیست"})
        self.assertEqual(caught.exception.error_code, USER_NOT_FOUND)

    def test_update_without_writable_fields_is_invalid(self) -> None:
        with self.assertRaises(InvalidInputError) as caught:
            update_user({"id": 1})
        self.assertEqual(caught.exception.error_code, INVALID_INPUT)

    def test_delete_removes_row_then_fetch_is_not_found(self) -> None:
        new_id = insert_temp_user()
        deleted_id = delete_user(new_id)
        self.assertEqual(deleted_id, new_id)
        with self.assertRaises(UserNotFoundError):
            fetch_user(new_id)

    def test_duplicate_email_is_invalid_input(self) -> None:
        email = unique_email("dup")
        first_id = insert_temp_user(email=email)
        try:
            with self.assertRaises(InvalidInputError) as caught:
                insert_user(minimal_user(email=email))
            self.assertEqual(caught.exception.error_code, INVALID_INPUT)
            self.assertIn("ایمیل", caught.exception.message)
        finally:
            delete_temp_user(first_id)


class RolePermissionServiceTests(unittest.TestCase):
    """نقش و مجوز seed و اتصال موقت را روی PostgreSQL بررسی می‌کند."""

    def test_seed_roles_exist_and_system_flag_stays(self) -> None:
        records = fetch_roles(limit=50, offset=0)
        by_name = {row["name"]: row for row in records}
        for name in ("مدیر کل", "مدیر پروژه", "کاربر", "ناظر"):
            self.assertIn(name, by_name)
        self.assertTrue(by_name["مدیر کل"]["is_system_role"])
        self.assertTrue(by_name["مدیر پروژه"]["is_system_role"])
        self.assertTrue(by_name["کاربر"]["is_system_role"])

    def test_cannot_delete_or_rename_system_role(self) -> None:
        admin_id = fetch_seed_role_id("مدیر کل")
        with self.assertRaises(InvalidInputError):
            delete_role(admin_id)
        with self.assertRaises(InvalidInputError):
            update_role({"id": admin_id, "name": "جعلی"})
        remaining = fetch_role(admin_id)
        self.assertEqual(remaining["name"], "مدیر کل")

    def test_insert_custom_role_and_permission_then_cleanup(self) -> None:
        role_id = insert_role({"name": unique_role_name(), "is_active": True})
        resource, action = unique_permission_pair()
        permission_id = insert_permission(
            {
                "name": f"مجوز {resource}",
                "resource": resource,
                "action": action,
            }
        )
        user_id = insert_temp_user()
        try:
            link_id = insert_role_permission(
                {"role_id": role_id, "permission_id": permission_id}
            )
            self.assertGreater(link_id, 0)
            assignment_id = insert_user_role(
                {"user_id": user_id, "role_id": role_id}
            )
            self.assertGreater(assignment_id, 0)
            listed = fetch_permissions(limit=50, offset=0)
            self.assertIn(permission_id, {row["id"] for row in listed})
        finally:
            delete_temp_user(user_id)
            delete_temp_role(role_id)
            delete_temp_permission(permission_id)


class ProjectServiceTests(unittest.TestCase):
    """درج پروژه روی Postgres و عضو شدن خودکار سازنده را بررسی می‌کند."""

    def test_insert_creates_project_and_manager_membership(self) -> None:
        user_id = insert_temp_user(last_name="سازنده-پروژه")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=user_id,
            )
            self.assertGreater(project_id, 0)
            row = fetch_project(project_id)
            self.assertEqual(row["created_by"], user_id)
            self.assertEqual(row["project_type_name"], "نرم‌افزاری")
            members = fetch_project_members(project_id, limit=10, offset=0)
            self.assertEqual(len(members), 1)
            self.assertEqual(members[0]["user_id"], user_id)
            self.assertEqual(members[0]["project_role_name"], "مدیر پروژه")
            scoped = fetch_projects_for_actor(user_id, limit=50, offset=0)
            self.assertIn(project_id, {item["id"] for item in scoped})
            stranger_id = insert_temp_user(last_name="غریبه")
            try:
                other = fetch_projects_for_actor(stranger_id, limit=50, offset=0)
                self.assertNotIn(project_id, {item["id"] for item in other})
            finally:
                delete_temp_user(stranger_id)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(user_id)

    def test_unknown_project_type_is_invalid_input(self) -> None:
        user_id = insert_temp_user()
        try:
            with self.assertRaises(InvalidInputError) as caught:
                insert_project(
                    {
                        "name": unique_project_name(),
                        "project_type": "نوع‌ناموجود",
                        "project_status": "در حال اجرا",
                    },
                    created_by=user_id,
                )
            self.assertEqual(caught.exception.error_code, INVALID_INPUT)
        finally:
            delete_temp_user(user_id)

    def test_delete_empty_project_then_fetch_is_not_found(self) -> None:
        user_id = insert_temp_user(last_name="حذف-پروژه")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("حذف-سرویس"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=user_id,
            )
            deleted = delete_project(project_id, actor_id=user_id)
            self.assertEqual(deleted, project_id)
            with self.assertRaises(ProjectNotFoundError) as caught:
                fetch_project(project_id)
            self.assertEqual(caught.exception.error_code, PROJECT_NOT_FOUND)
            project_id = None
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(user_id)

    def test_delete_project_with_task_soft_cancels(self) -> None:
        user_id = insert_temp_user(last_name="حذف-با-کار")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("حذف-با-کار"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=user_id,
            )
            insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("مانع"),
                    "status": "شروع نشده",
                    "priority": "کم",
                    "importance": "کم",
                },
                created_by=user_id,
            )
            deleted = delete_project(project_id, actor_id=user_id)
            self.assertEqual(deleted, project_id)
            with self.assertRaises(ProjectNotFoundError):
                fetch_project(project_id)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(user_id)


class TaskServiceTests(unittest.TestCase):
    """درج وظیفه و پیگیری جدا روی Postgres را بررسی می‌کند."""

    def test_insert_requires_active_member_assignee(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-وظیفه")
        stranger_id = insert_temp_user(last_name="غریبه-مسئول")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس-وظیفه"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("داشبورد"),
                    "status": "شروع نشده",
                    "priority": "فوری",
                    "importance": "حیاتی",
                    "assigned_to_user_id": owner_id,
                },
                created_by=owner_id,
            )
            row = fetch_task(task_id)
            self.assertEqual(row["assigned_to_user_id"], owner_id)
            self.assertEqual(row["priority_name"], "فوری")
            self.assertEqual(row["importance_name"], "حیاتی")
            scoped = fetch_tasks_for_actor(owner_id, limit=50, offset=0)
            self.assertIn(task_id, {item["id"] for item in scoped})
            hidden = fetch_tasks_for_actor(stranger_id, limit=50, offset=0)
            self.assertNotIn(task_id, {item["id"] for item in hidden})
            with self.assertRaises(InvalidInputError) as caught:
                insert_task(
                    {
                        "project_id": project_id,
                        "title": unique_task_title(),
                        "status": "شروع نشده",
                        "priority": "کم",
                        "importance": "کم",
                        "assigned_to_user_id": stranger_id,
                    },
                    created_by=owner_id,
                )
            self.assertEqual(caught.exception.error_code, INVALID_INPUT)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(stranger_id)
            delete_temp_user(owner_id)

    def test_follow_up_is_separate_from_status_update(self) -> None:
        owner_id = insert_temp_user(last_name="پیگیری-سازنده")
        member_id = insert_temp_user(last_name="عضو-مسئول")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name(),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": member_id,
                    "project_role": "عضو",
                }
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title(),
                    "status": "شروع نشده",
                    "priority": "متوسط",
                    "importance": "متوسط",
                    "assigned_to_user_id": member_id,
                },
                created_by=owner_id,
            )
            self.assertEqual(count_task_follow_ups(task_id), 0)
            first = insert_task_follow_up(
                {
                    "task_id": task_id,
                    "follow_up_type": "تماس",
                    "status": "منتظر پاسخ",
                    "note": "تماس اول",
                },
                followed_by=owner_id,
            )
            second = insert_task_follow_up(
                {
                    "task_id": task_id,
                    "follow_up_type": "پیام",
                    "status": "پاسخ داده",
                    "note": "پیام دوم",
                },
                followed_by=owner_id,
            )
            self.assertGreater(first, 0)
            self.assertGreater(second, 0)
            self.assertEqual(count_task_follow_ups(task_id), 2)
            update_task({"id": task_id, "status": "تکمیل شده"})
            self.assertEqual(count_task_follow_ups(task_id), 2)
            listed = fetch_task_follow_ups(task_id, limit=10, offset=0)
            self.assertEqual(len(listed), 2)
            types = {row["follow_up_type_name"] for row in listed}
            self.assertEqual(types, {"تماس", "پیام"})
            row = fetch_task(task_id)
            self.assertEqual(row["status_name"], "تکمیل شده")
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(member_id)
            delete_temp_user(owner_id)

    def test_delete_task_then_fetch_is_not_found(self) -> None:
        owner_id = insert_temp_user(last_name="حذف-وظیفه")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("حذف-کار"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("حذف-شو"),
                    "status": "شروع نشده",
                    "priority": "کم",
                    "importance": "کم",
                    "assigned_to_user_id": owner_id,
                },
                created_by=owner_id,
            )
            insert_task_item(
                {
                    "task_id": task_id,
                    "title": "زیرکار CASCADE",
                },
                actor_id=owner_id,
            )
            deleted = delete_task(task_id, actor_id=owner_id)
            self.assertEqual(deleted, task_id)
            with self.assertRaises(TaskNotFoundError) as caught:
                fetch_task(task_id)
            self.assertEqual(caught.exception.error_code, TASK_NOT_FOUND)
            with self.assertRaises(TaskNotFoundError):
                fetch_task_items(task_id)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(owner_id)


class TaskItemServiceTests(unittest.TestCase):
    """درج تو در تو، تیک، قید مسئول و CASCADE روی Postgres."""

    def test_assignee_can_nest_and_member_cannot_change(self) -> None:
        owner_id = insert_temp_user(last_name="مسئول-زیرکار")
        member_id = insert_temp_user(last_name="عضو-زیرکار")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس-زیرکار"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": member_id,
                    "project_role": "عضو",
                }
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("داشبورد"),
                    "status": "شروع نشده",
                    "priority": "متوسط",
                    "importance": "زیاد",
                    "assigned_to_user_id": owner_id,
                },
                created_by=owner_id,
            )
            parent_id = insert_task_item(
                {
                    "task_id": task_id,
                    "title": "وایر فریم",
                    "sort_order": 0,
                },
                actor_id=owner_id,
            )
            child_id = insert_task_item(
                {
                    "task_id": task_id,
                    "title": unique_task_item_title("موبایل"),
                    "parent_item_id": parent_id,
                },
                actor_id=owner_id,
            )
            complete_task_item(child_id, actor_id=owner_id)
            payload = fetch_task_items(task_id)
            by_id = {row["id"]: row for row in payload["records"]}
            self.assertTrue(by_id[child_id]["is_completed"])
            self.assertEqual(payload["tree"][0]["id"], parent_id)
            self.assertEqual(payload["tree"][0]["children"][0]["id"], child_id)
            with self.assertRaises(PermissionDeniedError) as caught:
                insert_task_item(
                    {
                        "task_id": task_id,
                        "title": unique_task_item_title("ممنوع"),
                    },
                    actor_id=member_id,
                )
            self.assertEqual(caught.exception.error_code, PERMISSION_DENIED)
            delete_task_item(parent_id, actor_id=owner_id)
            remaining = fetch_task_items(task_id)
            remaining_ids = {row["id"] for row in remaining["records"]}
            self.assertNotIn(parent_id, remaining_ids)
            self.assertNotIn(child_id, remaining_ids)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(member_id)
            delete_temp_user(owner_id)


class MessageContactServiceTests(unittest.TestCase):
    """درج مخاطب خارجی، چت پروژه، پیام با دو گیرنده، و XOR روی Postgres."""

    def test_external_contact_is_not_a_user(self) -> None:
        phone = unique_phone()
        contact_id = insert_external_contact(
            {
                "name": unique_contact_name("پیمانکار"),
                "phone": phone,
            }
        )
        try:
            contact = fetch_external_contact(contact_id)
            self.assertEqual(contact["phone"], phone)
            self.assertTrue(contact["is_active"])
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM users WHERE phone = %s",
                        [phone],
                    )
                    self.assertIsNone(cursor.fetchone())
                    cursor.execute(
                        "SELECT id FROM users WHERE id = %s",
                        [contact_id],
                    )
                    user_row = cursor.fetchone()
                    if user_row is not None:
                        cursor.execute(
                            "SELECT phone FROM users WHERE id = %s",
                            [contact_id],
                        )
                        self.assertNotEqual(cursor.fetchone()[0], phone)
            finally:
                connection.close()
        finally:
            delete_temp_external_contact(contact_id)

    def test_project_chat_message_recipients_and_scope(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-چت")
        member_id = insert_temp_user(last_name="عضو-چت")
        stranger_id = insert_temp_user(last_name="غریبه-چت")
        project_id = None
        chat_id = None
        contact_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس-پیام"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": member_id,
                    "project_role": "عضو",
                }
            )
            contact_id = insert_external_contact(
                {
                    "name": unique_contact_name("پیمانکار"),
                    "phone": unique_phone(),
                }
            )
            chat_id = insert_chat(
                {
                    "title": unique_chat_title("پروژه"),
                    "project_id": project_id,
                    "chat_type": "گفتگوی پروژه",
                },
                created_by=owner_id,
            )
            insert_chat_member({"chat_id": chat_id, "user_id": member_id})
            members = fetch_chat_members(chat_id, limit=10, offset=0)
            self.assertEqual({row["user_id"] for row in members}, {owner_id, member_id})
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("نظر"),
                    "status": "شروع نشده",
                    "priority": "متوسط",
                    "importance": "متوسط",
                    "assigned_to_user_id": owner_id,
                },
                created_by=owner_id,
            )
            message_id = insert_message(
                {
                    "chat_id": chat_id,
                    "task_id": task_id,
                    "text": "پیگیری قرارداد را امروز انجام دهید.",
                    "recipient_user_id": member_id,
                    "recipient_external_contact_id": contact_id,
                },
                sender_user_id=owner_id,
            )
            message = fetch_message(message_id)
            self.assertEqual(message["text"], "پیگیری قرارداد را امروز انجام دهید.")
            self.assertEqual(message["task_id"], task_id)
            self.assertNotIn("content_id", message)
            recipients = fetch_message_recipients(message_id, limit=10, offset=0)
            self.assertEqual(len(recipients), 2)
            self.assertEqual(
                {row["user_id"] for row in recipients if row["user_id"] is not None},
                {member_id},
            )
            self.assertEqual(
                {
                    row["external_contact_id"]
                    for row in recipients
                    if row["external_contact_id"] is not None
                },
                {contact_id},
            )
            scoped = fetch_messages_for_actor(owner_id, limit=50, offset=0)
            self.assertIn(message_id, {item["id"] for item in scoped})
            hidden = fetch_messages_for_actor(stranger_id, limit=50, offset=0)
            self.assertNotIn(message_id, {item["id"] for item in hidden})
            chats = fetch_chats_for_actor(stranger_id, limit=50, offset=0)
            self.assertNotIn(chat_id, {item["id"] for item in chats})
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(stranger_id)
            delete_temp_user(member_id)
            delete_temp_user(owner_id)

    def test_recipient_xor_and_missing_recipient_are_invalid(self) -> None:
        owner_id = insert_temp_user(last_name="xor-پیام")
        project_id = None
        chat_id = None
        contact_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name(),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            contact_id = insert_external_contact(
                {"name": unique_contact_name(), "phone": unique_phone()}
            )
            chat_id = insert_chat(
                {
                    "title": unique_chat_title(),
                    "project_id": project_id,
                    "chat_type": "گفتگوی پروژه",
                },
                created_by=owner_id,
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("xor"),
                    "status": "شروع نشده",
                    "priority": "متوسط",
                    "importance": "متوسط",
                    "assigned_to_user_id": owner_id,
                },
                created_by=owner_id,
            )
            message_id = insert_message(
                {
                    "chat_id": chat_id,
                    "task_id": task_id,
                    "text": "یک گیرنده معتبر",
                    "recipient_user_id": owner_id,
                },
                sender_user_id=owner_id,
            )
            with self.assertRaises(InvalidInputError) as both:
                insert_message_recipient(
                    {
                        "message_id": message_id,
                        "user_id": owner_id,
                        "external_contact_id": contact_id,
                    }
                )
            self.assertEqual(both.exception.error_code, INVALID_INPUT)
            with self.assertRaises(InvalidInputError) as neither:
                insert_message_recipient({"message_id": message_id})
            self.assertEqual(neither.exception.error_code, INVALID_INPUT)
            with self.assertRaises(InvalidInputError) as missing:
                insert_message(
                    {
                        "chat_id": chat_id,
                        "task_id": task_id,
                        "text": "بدون گیرنده",
                    },
                    sender_user_id=owner_id,
                )
            self.assertEqual(missing.exception.error_code, INVALID_INPUT)
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(owner_id)


    def test_private_chat_message_has_no_task(self) -> None:
        owner_id = insert_temp_user(last_name="خصوصی-پیام")
        peer_id = insert_temp_user(last_name="گیرنده-خصوصی")
        chat_id = None
        try:
            chat_id = insert_chat(
                {
                    "title": unique_chat_title("خصوصی"),
                    "chat_type": "گفتگوی خصوصی",
                },
                created_by=owner_id,
            )
            insert_chat_member({"chat_id": chat_id, "user_id": peer_id})
            message_id = insert_message(
                {
                    "chat_id": chat_id,
                    "text": "سلام خصوصی",
                    "recipient_user_id": peer_id,
                },
                sender_user_id=owner_id,
            )
            message = fetch_message(message_id)
            self.assertEqual(message["text"], "سلام خصوصی")
            self.assertIsNone(message["task_id"])
            with self.assertRaises(InvalidInputError):
                insert_message(
                    {
                        "chat_id": chat_id,
                        "task_id": 1,
                        "text": "با تسک",
                        "recipient_user_id": peer_id,
                    },
                    sender_user_id=owner_id,
                )
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            delete_temp_user(peer_id)
            delete_temp_user(owner_id)

    def test_project_chat_message_without_task(self) -> None:
        owner_id = insert_temp_user(last_name="گزارش-پروژه")
        project_id = None
        chat_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name(),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            chat_id = insert_chat(
                {
                    "title": unique_chat_title("پروژه"),
                    "project_id": project_id,
                    "chat_type": "گفتگوی پروژه",
                },
                created_by=owner_id,
            )
            message_id = insert_message(
                {
                    "chat_id": chat_id,
                    "text": "وضعیت پروژه بدون اشاره به وظیفه.",
                    "recipient_user_id": owner_id,
                },
                sender_user_id=owner_id,
            )
            message = fetch_message(message_id)
            self.assertEqual(message["text"], "وضعیت پروژه بدون اشاره به وظیفه.")
            self.assertIsNone(message["task_id"])
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(owner_id)


class PerformanceActionServiceTests(unittest.TestCase):
    """ثبت اقدام امتیاز را در scores می‌نویسد و با جمع اقدام‌ها یکی می‌ماند."""

    def test_score_rows_match_action_scores(self) -> None:
        owner_id = insert_temp_user(first_name="علی", last_name="ارزیاب")
        subject_id = insert_temp_user(first_name="رضا", last_name="ارزیابی‌شونده")
        project_id = None
        account_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("عملکرد"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            account_id = insert_temp_account(unique_account_name("پاداش سرویس"))
            insert_performance_action(
                {
                    "user_id": subject_id,
                    "project_id": project_id,
                    "action_type": "تقدیر",
                    "reason": "کیفیت کار",
                    "score": 4,
                },
                created_by=owner_id,
            )
            insert_performance_action(
                {
                    "user_id": subject_id,
                    "project_id": project_id,
                    "action_type": "پاداش نقدی",
                    "reason": "تحویل زودتر",
                    "score": 6,
                    "amount": 500_000,
                    "account_id": account_id,
                },
                created_by=owner_id,
            )
            totals = score_totals_for_user(subject_id)
            self.assertEqual(totals["scores_total"], 10)
            self.assertEqual(totals["actions_total"], 10)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            if account_id is not None:
                delete_temp_account(account_id)
            delete_temp_user(subject_id)
            delete_temp_user(owner_id)


class ContentServiceTests(unittest.TestCase):
    """درج متن و صوت در contents را روی Postgres می‌سنجد."""

    def test_insert_text_and_voice(self) -> None:
        owner_id = insert_temp_user(last_name="محتوا-سرویس")
        try:
            text_id = insert_content(
                {"content_kind": "TEXT", "text_body": "یادداشت جلسه"},
                created_by=owner_id,
            )
            row = fetch_content(text_id)
            self.assertEqual(row["content_kind_code"], "TEXT")
            self.assertEqual(row["text_body"], "یادداشت جلسه")
            self.assertIsNone(row["storage_key"])

            voice_id = insert_content(
                {
                    "content_kind": "VOICE",
                    "storage_key": unique_storage_key("svc"),
                    "original_filename": "note.ogg",
                    "mime_type": "audio/ogg",
                    "file_size_bytes": 512,
                },
                created_by=owner_id,
            )
            audio = fetch_content(voice_id)
            self.assertEqual(audio["content_kind_code"], "VOICE")
            self.assertEqual(audio["original_filename"], "note.ogg")

            with self.assertRaises(InvalidInputError):
                insert_content(
                    {"content_kind": "TEXT", "text_body": "  "},
                    created_by=owner_id,
                )
        finally:
            delete_temp_user(owner_id)

    def test_missing_content_raises(self) -> None:
        from errors.crud import ContentNotFoundError

        with self.assertRaises(ContentNotFoundError) as caught:
            fetch_content(9_999_999)
        self.assertEqual(caught.exception.error_code, CONTENT_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
