"""تست ثبت ابزار تعریف یادآوری و پاکت JSON روی دیتابیس واقعی."""

from pathlib import Path
import asyncio
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import (
    INVALID_INPUT,
    PERMISSION_DENIED,
    REMINDER_NOT_FOUND,
    format_error,
    format_success,
)
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_CREATE_REMINDER,
    TITLE_LIST_EXECUTION_LOGS,
    TITLE_LIST_FOLLOW_UP_STATES,
    TITLE_LIST_REMINDERS,
    TITLE_RETRY_REMINDER,
    TITLE_SEND_REMINDER,
    WRITE_REMINDER,
)
from mcp_server.register import register_reminder_tools
from mcp_server.tools.dispatch.retry_reminder import run_retry_reminder
from mcp_server.tools.dispatch.send_reminder import run_send_reminder
from mcp_server.tools.execution_log.list_execution_logs import (
    run_list_execution_logs,
)
from mcp_server.tools.follow_up_state.list_follow_up_states import (
    run_list_follow_up_states,
)
from mcp_server.tools.reminder.create_reminder import run_create_reminder
from mcp_server.tools.reminder.get_reminder import run_get_reminder
from mcp_server.tools.reminder.list_reminders import run_list_reminders
from mcp_server.tools.reminder.update_reminder import run_update_reminder
from services.connection import open_connection
from services.external_contact import insert_external_contact
from services.project import insert_project
from services.project_member import insert_project_member
from tests.conftest import (
    assign_seed_role,
    bind_actor_as_role,
    delete_temp_external_contact,
    delete_temp_project,
    delete_temp_reminder,
    delete_temp_user,
    insert_temp_user,
    unique_contact_name,
    unique_phone,
    unique_project_name,
    unique_reminder_title,
)


_REGISTERED_TOOLS = {
    "create_reminder",
    "get_reminder",
    "list_reminders",
    "update_reminder",
    "list_follow_up_states",
    "send_reminder",
    "retry_reminder",
    "list_execution_logs",
}

_TOMORROW_NINE = "2026-09-16T09:00:00"


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت فقط ابزارهای تعریف یادآوری را بررسی می‌کند."""

    def test_metadata_names_management_reminder(self) -> None:
        self.assertEqual(SERVER_NAME, "management-reminder")
        self.assertEqual(SERVER_TITLE, "یادآوری سامانه مدیریت")

    def test_register_adds_definition_and_dispatch_tools(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_reminder_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(names, _REGISTERED_TOOLS)
        self.assertNotIn("create_execution_log", names)

    def test_server_module_lists_registered_tools(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(mcp.name, SERVER_NAME)
        names = {tool.name for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(names, _REGISTERED_TOOLS)


class ErrorEnvelopeTests(unittest.TestCase):
    def test_success_envelope(self) -> None:
        payload = format_success("ثبت شد", id=7)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["id"], 7)

    def test_unknown_maps_to_database_error(self) -> None:
        payload = format_error(RuntimeError("boom"))
        self.assertEqual(payload["error_code"], "DATABASE_ERROR")


class ReminderToolTests(unittest.TestCase):
    """تعریف یادآوری، گیرنده، follow_up_states، XOR، و نبود execution_logs."""

    def test_create_reminder_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_reminder"]
        self.assertEqual(tool.title, TITLE_CREATE_REMINDER)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertEqual(
            tool.annotations.read_only_hint,
            WRITE_REMINDER.read_only_hint,
        )
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("title", required)
        self.assertIn("message_template", required)
        self.assertIn("scheduled_at", required)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("target_user_id", properties)
        self.assertIn("target_external_contact_id", properties)
        self.assertNotIn("content_id", properties)
        self.assertNotIn("task_item_id", properties)
        self.assertNotIn("created_by_user_id", properties)
        list_tool = by_name["list_reminders"]
        self.assertEqual(list_tool.title, TITLE_LIST_REMINDERS)
        self.assertTrue(list_tool.annotations.read_only_hint)
        states_tool = by_name["list_follow_up_states"]
        self.assertEqual(states_tool.title, TITLE_LIST_FOLLOW_UP_STATES)
        send_tool = by_name["send_reminder"]
        self.assertEqual(send_tool.title, TITLE_SEND_REMINDER)
        self.assertFalse(send_tool.annotations.read_only_hint)
        self.assertEqual(
            send_tool.annotations.read_only_hint,
            WRITE_REMINDER.read_only_hint,
        )
        retry_tool = by_name["retry_reminder"]
        self.assertEqual(retry_tool.title, TITLE_RETRY_REMINDER)
        logs_tool = by_name["list_execution_logs"]
        self.assertEqual(logs_tool.title, TITLE_LIST_EXECUTION_LOGS)
        self.assertTrue(logs_tool.annotations.read_only_hint)

    def test_define_reminder_for_user_and_external_without_sending(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="گیرنده")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        contact_id = None
        reminder_id = None
        mohammad = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سایت"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=ali.user_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": reza_id,
                    "project_role": "عضو",
                }
            )
            contact_id = insert_external_contact(
                {
                    "name": unique_contact_name("پیمانکار"),
                    "phone": unique_phone(),
                }
            )
            created = run_create_reminder(
                title=unique_reminder_title("گزارش‌هفتگی"),
                message_template="گزارش هفتگی را بفرستید.",
                scheduled_at=_TOMORROW_NINE,
                reminder_type="یک‌باره",
                frequency="یک‌باره",
                project_id=project_id,
                target_user_id=reza_id,
                target_external_contact_id=contact_id,
            )
            self.assertEqual(created["status"], "success")
            reminder_id = created["id"]
            fetched = run_get_reminder(id=reminder_id)
            self.assertEqual(fetched["status"], "success")
            self.assertIn("گزارش هفتگی", fetched["message_template"])
            self.assertEqual(fetched["reminder_type_name"], "یک‌باره")
            self.assertEqual(fetched["frequency_name"], "یک‌باره")
            self.assertEqual(fetched["status_name"], "فعال")
            self.assertEqual(fetched["project_id"], project_id)
            self.assertNotIn("content_id", fetched)
            self.assertNotIn("task_item_id", fetched)
            states = run_list_follow_up_states(reminder_id=reminder_id, limit=10)
            self.assertEqual(states["status"], "success")
            self.assertEqual(len(states["records"]), 2)
            self.assertEqual(
                {row["status_name"] for row in states["records"]},
                {"در انتظار"},
            )
            self.assertEqual(
                {row["attempt_count"] for row in states["records"]},
                {0},
            )
            self.assertEqual(
                {
                    row["user_id"]
                    for row in states["records"]
                    if row["user_id"] is not None
                },
                {reza_id},
            )
            self.assertEqual(
                {
                    row["external_contact_id"]
                    for row in states["records"]
                    if row["external_contact_id"] is not None
                },
                {contact_id},
            )
            for row in states["records"]:
                self.assertTrue(
                    (row["user_id"] is None) != (row["external_contact_id"] is None)
                )
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM execution_logs WHERE reminder_id = %s",
                        [reminder_id],
                    )
                    self.assertEqual(cursor.fetchone()[0], 0)
            finally:
                connection.close()
            missing_target = run_create_reminder(
                title=unique_reminder_title(),
                message_template="بدون گیرنده",
                scheduled_at=_TOMORROW_NINE,
                reminder_type="یک‌باره",
                frequency="یک‌باره",
            )
            self.assertEqual(missing_target["status"], "error")
            self.assertEqual(missing_target["error_code"], INVALID_INPUT)
            updated = run_update_reminder(id=reminder_id, status="متوقف")
            self.assertEqual(updated["status"], "success")
            after = run_get_reminder(id=reminder_id)
            self.assertEqual(after["status_name"], "متوقف")
            listed = run_list_reminders(project_id=project_id, limit=50)
            self.assertIn(reminder_id, {row["id"] for row in listed["records"]})
            mohammad = bind_actor_as_role("مدیر پروژه")
            outsider = run_list_reminders(limit=50, offset=0)
            self.assertNotIn(
                reminder_id,
                {row["id"] for row in outsider["records"]},
            )
            hidden = run_get_reminder(id=reminder_id)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
        finally:
            if mohammad is not None:
                mohammad.close()
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_personal_reminder_and_weekly_manager_example(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reminder_id = None
        try:
            created = run_create_reminder(
                title=unique_reminder_title("دوشنبه"),
                message_template="هر دوشنبه وضعیت پروژه را بفرستید.",
                scheduled_at="2026-09-21T09:00:00",
                reminder_type="دوره‌ای",
                frequency="هفتگی",
                target_user_id=ali.user_id,
            )
            self.assertEqual(created["status"], "success")
            reminder_id = created["id"]
            fetched = run_get_reminder(id=reminder_id)
            self.assertIsNone(fetched["project_id"])
            self.assertEqual(fetched["frequency_name"], "هفتگی")
            self.assertEqual(fetched["next_run_at"][:19], "2026-09-21T09:00:00")
            states = run_list_follow_up_states(reminder_id=reminder_id)
            self.assertEqual(len(states["records"]), 1)
            self.assertEqual(states["records"][0]["user_id"], ali.user_id)
            self.assertEqual(states["records"][0]["status_name"], "در انتظار")
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            ali.close()

    def test_missing_reminder_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            missing = run_get_reminder(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], REMINDER_NOT_FOUND)
        finally:
            ali.close()

    def test_send_reminder_writes_log_and_is_idempotent(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="گیرنده-ارسال")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        reminder_id = None
        message = "گزارش هفتگی را بفرستید."
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("اعلان"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=ali.user_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": reza_id,
                    "project_role": "عضو",
                }
            )
            created = run_create_reminder(
                title=unique_reminder_title("ارسال"),
                message_template=message,
                scheduled_at=_TOMORROW_NINE,
                reminder_type="یک‌باره",
                frequency="یک‌باره",
                target_user_id=reza_id,
            )
            self.assertEqual(created["status"], "success")
            reminder_id = created["id"]
            first = run_send_reminder(reminder_id=reminder_id)
            self.assertEqual(first["status"], "success")
            self.assertEqual(first["sent_count"], 1)
            self.assertEqual(first["replayed_count"], 0)
            self.assertEqual(len(first["records"]), 1)
            log_row = first["records"][0]
            self.assertEqual(log_row["channel"], "INTERNAL")
            self.assertEqual(log_row["status"], "SENT")
            self.assertEqual(log_row["attempt_number"], 1)
            self.assertEqual(log_row["user_id"], reza_id)
            self.assertFalse(log_row["replayed"])
            self.assertIsNotNone(log_row["idempotency_key"])
            states = run_list_follow_up_states(reminder_id=reminder_id)
            self.assertEqual(len(states["records"]), 1)
            self.assertEqual(states["records"][0]["status_name"], "در انتظار")
            self.assertEqual(states["records"][0]["attempt_count"], 1)
            self.assertIsNotNone(states["records"][0]["last_sent_at"])
            logs = run_list_execution_logs(reminder_id=reminder_id)
            self.assertEqual(len(logs["records"]), 1)
            self.assertEqual(logs["records"][0]["id"], log_row["id"])
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM notifications
                        WHERE user_id = %s AND message = %s
                        """,
                        [reza_id, message],
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
            finally:
                connection.close()
            second = run_send_reminder(reminder_id=reminder_id)
            self.assertEqual(second["status"], "success")
            self.assertEqual(second["sent_count"], 0)
            self.assertEqual(second["replayed_count"], 1)
            self.assertTrue(second["records"][0]["replayed"])
            self.assertEqual(second["records"][0]["id"], log_row["id"])
            logs_again = run_list_execution_logs(reminder_id=reminder_id)
            self.assertEqual(len(logs_again["records"]), 1)
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM notifications
                        WHERE user_id = %s AND message = %s
                        """,
                        [reza_id, message],
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT COUNT(*) FROM execution_logs WHERE reminder_id = %s",
                        [reminder_id],
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
            finally:
                connection.close()
            retried = run_retry_reminder(reminder_id=reminder_id)
            self.assertEqual(retried["status"], "success")
            self.assertEqual(retried["sent_count"], 1)
            self.assertEqual(retried["records"][0]["attempt_number"], 2)
            logs_retry = run_list_execution_logs(reminder_id=reminder_id)
            self.assertEqual(len(logs_retry["records"]), 2)
            telegram = run_send_reminder(
                reminder_id=reminder_id,
                channel="TELEGRAM",
            )
            self.assertEqual(telegram["status"], "error")
            self.assertEqual(telegram["error_code"], INVALID_INPUT)
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_send_denied_without_dispatch_permission(self) -> None:
        owner = bind_actor_as_role("مدیر پروژه")
        reminder_id = None
        reader = None
        try:
            created = run_create_reminder(
                title=unique_reminder_title("بدون-ارسال"),
                message_template="نباید برود.",
                scheduled_at=_TOMORROW_NINE,
                reminder_type="یک‌باره",
                frequency="یک‌باره",
                target_user_id=owner.user_id,
            )
            self.assertEqual(created["status"], "success")
            reminder_id = created["id"]
            reader = bind_actor_as_role("کاربر")
            denied = run_send_reminder(reminder_id=reminder_id)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
        finally:
            if reader is not None:
                reader.close()
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            owner.close()


if __name__ == "__main__":
    unittest.main()
