"""تست ثبت ابزار جلسه و پاکت JSON روی دیتابیس واقعی."""

from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import sys
import unittest
import uuid

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import (
    INVALID_INPUT,
    MEETING_SLOT_CONFLICT,
    PERMISSION_DENIED,
    format_error,
    format_success,
)
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_CREATE_MEETING_SCHEDULE,
    TITLE_GENERATE_MEETINGS,
    TITLE_RECORD_MEETING,
    TITLE_SYNC_MEETING,
    WRITE_MEETING,
)
from mcp_server.register import register_meeting_tools
from mcp_server.tools.generate_meetings.generate_meetings import run_generate_meetings
from mcp_server.tools.meeting.cancel_meeting import run_cancel_meeting
from mcp_server.tools.meeting.create_meeting import run_create_meeting
from mcp_server.tools.meeting.get_meeting import run_get_meeting
from mcp_server.tools.meeting.list_meetings import run_list_meetings
from mcp_server.tools.meeting.record_meeting import run_record_meeting
from mcp_server.tools.meeting.sync_meeting import run_sync_meeting
from mcp_server.tools.meeting_participant.create_meeting_participant import (
    run_create_meeting_participant,
)
from mcp_server.tools.meeting_schedule.create_meeting_schedule import (
    run_create_meeting_schedule,
)
from mcp_server.tools.meeting_schedule.get_meeting_schedule import (
    run_get_meeting_schedule,
)
from services.content import insert_content
from services.external_contact import insert_external_contact
from services.project import insert_project
from services.project_member import insert_project_member
from services.task import fetch_task
from tests.conftest import (
    bind_actor_as_role,
    delete_temp_external_contact,
    delete_temp_meeting,
    delete_temp_project,
    delete_temp_user,
    insert_temp_user,
    unique_contact_name,
    unique_meeting_title,
    unique_phone,
    unique_project_name,
)


_REGISTERED_TOOLS = {
    "create_meeting_schedule",
    "get_meeting_schedule",
    "list_meeting_schedules",
    "create_meeting",
    "get_meeting",
    "list_meetings",
    "cancel_meeting",
    "create_meeting_participant",
    "generate_meetings",
    "record_meeting",
    "sync_meeting",
}


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت فقط ابزارهای برنامه‌ریزی جلسه را بررسی می‌کند."""

    def test_metadata_names_management_meeting(self) -> None:
        self.assertEqual(SERVER_NAME, "management-meeting")
        self.assertEqual(SERVER_TITLE, "جلسات سامانه مدیریت")

    def test_register_adds_planning_and_sync_tools(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_meeting_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(names, _REGISTERED_TOOLS)
        self.assertIn("record_meeting", names)
        self.assertIn("sync_meeting", names)
        self.assertNotIn("create_meeting_sync_item", names)

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


class MeetingToolTests(unittest.TestCase):
    """الگو، generate هفتهٔ بعد، تداخل، XOR، و نبود ابزار ضبط."""

    def test_schedule_tool_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_meeting_schedule"]
        self.assertEqual(tool.title, TITLE_CREATE_MEETING_SCHEDULE)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertEqual(
            tool.annotations.read_only_hint,
            WRITE_MEETING.read_only_hint,
        )
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("start_time", required)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("day_name", properties)
        self.assertIn("day_of_week", properties)
        self.assertNotIn("content_id", properties)
        generate_tool = by_name["generate_meetings"]
        self.assertEqual(generate_tool.title, TITLE_GENERATE_MEETINGS)
        record_tool = by_name["record_meeting"]
        self.assertEqual(record_tool.title, TITLE_RECORD_MEETING)
        self.assertFalse(record_tool.annotations.read_only_hint)
        sync_tool = by_name["sync_meeting"]
        self.assertEqual(sync_tool.title, TITLE_SYNC_MEETING)
        cancel_tool = by_name["cancel_meeting"]
        self.assertFalse(cancel_tool.annotations.read_only_hint)

    def test_wednesday_schedule_generate_conflict_and_participants(self) -> None:
        ahmad = bind_actor_as_role("مدیر پروژه")
        teammate_id = insert_temp_user(last_name="علی-جلسه")
        contact_id = None
        schedule_id = None
        meeting_id = None
        outsider = None
        try:
            created = run_create_meeting_schedule(
                meeting_type="جلسه تیم",
                day_name="چهارشنبه",
                start_time="10:00",
                duration_minutes=60,
            )
            self.assertEqual(created["status"], "success")
            schedule_id = created["id"]
            loaded = run_get_meeting_schedule(id=schedule_id)
            self.assertEqual(loaded["day_of_week"], 4)
            self.assertEqual(loaded["start_time"], "10:00:00")

            first = run_generate_meetings(schedule_id=schedule_id, weeks_ahead=1)
            self.assertEqual(first["status"], "success")
            self.assertTrue(first["created"])
            meeting_id = first["id"]
            self.assertTrue(str(first["scheduled_at"]).startswith("20"))
            row = run_get_meeting(id=meeting_id)
            self.assertEqual(row["status_name"], "برنامه‌ریزی شده")
            self.assertIsNone(row["content_id"])
            self.assertEqual(row["sync_status"], "NOT_SYNCED")
            self.assertEqual(row["participants"], [])

            conflict = run_generate_meetings(schedule_id=schedule_id, weeks_ahead=1)
            self.assertEqual(conflict["status"], "success")
            self.assertFalse(conflict["created"])
            self.assertTrue(conflict["conflict"])
            self.assertIn("suggested_at", conflict)

            overlap = run_create_meeting(
                title=unique_meeting_title("هم‌زمان"),
                scheduled_at=row["scheduled_at"],
                meeting_type="مذاکره مدیران",
                duration_minutes=60,
            )
            self.assertEqual(overlap["status"], "error")
            self.assertEqual(overlap["error_code"], MEETING_SLOT_CONFLICT)
            self.assertIn("suggested_at", overlap)

            contact_id = insert_external_contact(
                {"name": unique_contact_name("طرف‌خارجی"), "phone": unique_phone()},
                actor_id=ahmad.user_id,
            )
            user_part = run_create_meeting_participant(
                meeting_id=meeting_id,
                user_id=teammate_id,
            )
            self.assertEqual(user_part["status"], "success")
            ext_part = run_create_meeting_participant(
                meeting_id=meeting_id,
                external_contact_id=contact_id,
            )
            self.assertEqual(ext_part["status"], "success")
            both = run_create_meeting_participant(
                meeting_id=meeting_id,
                user_id=teammate_id,
                external_contact_id=contact_id,
            )
            self.assertEqual(both["status"], "error")
            self.assertEqual(both["error_code"], INVALID_INPUT)
            with_people = run_get_meeting(id=meeting_id)
            self.assertEqual(len(with_people["participants"]), 2)

            listed = run_list_meetings(limit=50)
            self.assertIn(meeting_id, {item["id"] for item in listed["records"]})

            outsider = bind_actor_as_role("کاربر")
            hidden = run_get_meeting(id=meeting_id)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            outsider.close()
            outsider = None

            cancelled = run_cancel_meeting(id=meeting_id)
            self.assertEqual(cancelled["status"], "success")
            after = run_get_meeting(id=meeting_id)
            self.assertEqual(after["status_name"], "لغو شده")
        finally:
            if outsider is not None:
                outsider.close()
            if meeting_id is not None:
                delete_temp_meeting(meeting_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            delete_temp_user(teammate_id)
            ahmad.close()

    def test_record_and_sync_team_meeting_and_reject_private(self) -> None:
        ahmad = bind_actor_as_role("مدیر پروژه")
        teammate_id = insert_temp_user(last_name="مسئول-وظیفه")
        project_id = None
        team_id = None
        private_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("جلسه-همگام"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=ahmad.user_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": teammate_id,
                    "project_role": "عضو",
                },
                actor_id=ahmad.user_id,
            )
            slot = datetime(2028, 3, 1, 10, 0) + timedelta(
                minutes=int(uuid.uuid4().hex[:4], 16) % 200
            )
            created = run_create_meeting(
                title=unique_meeting_title("تیم-ضبط"),
                scheduled_at=slot.isoformat(),
                meeting_type="جلسه تیم",
                project_id=project_id,
                visibility="PROJECT",
            )
            self.assertEqual(created["status"], "success")
            team_id = created["id"]
            content_id = insert_content(
                {
                    "content_kind": "TEXT",
                    "text_body": "گزارش جلسه: داشبورد تا چهارشنبه تمام شود.",
                },
                created_by=ahmad.user_id,
            )
            recorded = run_record_meeting(id=team_id, content_id=content_id)
            self.assertEqual(recorded["status"], "success")
            loaded = run_get_meeting(id=team_id)
            self.assertEqual(loaded["status_name"], "ضبط شده")
            self.assertEqual(loaded["content_id"], content_id)

            synced = run_sync_meeting(
                id=team_id,
                decision_title="تمرکز روی داشبورد",
                decision_description="اسپرینت بعدی فقط داشبورد است.",
                assigned_to_user_id=teammate_id,
                task_title="اتمام داشبورد",
            )
            self.assertEqual(synced["status"], "success")
            self.assertEqual(synced["sync_status"], "SYNCED")
            self.assertIsNotNone(synced["task_id"])
            self.assertIsNone(synced.get("report_id"))
            task = fetch_task(synced["task_id"])
            self.assertEqual(task["assigned_to_user_id"], teammate_id)
            after_sync = run_get_meeting(id=team_id)
            self.assertEqual(after_sync["status_name"], "همگام‌سازی شده")
            self.assertEqual(after_sync["sync_status"], "SYNCED")
            self.assertEqual(len(after_sync["sync_items"]), 1)

            private = run_create_meeting(
                title=unique_meeting_title("مدیران-خصوصی"),
                scheduled_at=(slot + timedelta(hours=6)).isoformat(),
                meeting_type="مذاکره مدیران",
                visibility="PRIVATE",
            )
            self.assertEqual(private["status"], "success")
            private_id = private["id"]
            private_content = insert_content(
                {
                    "content_kind": "TEXT",
                    "text_body": "مذاکره اولیه بدون پروژه.",
                },
                created_by=ahmad.user_id,
            )
            recorded_private = run_record_meeting(
                id=private_id,
                content_id=private_content,
            )
            self.assertEqual(recorded_private["status"], "success")
            denied = run_sync_meeting(id=private_id)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], INVALID_INPUT)
            still = run_get_meeting(id=private_id)
            self.assertEqual(still["sync_status"], "NOT_SYNCED")
            self.assertEqual(still["sync_items"], [])
        finally:
            if team_id is not None:
                delete_temp_meeting(team_id)
            if private_id is not None:
                delete_temp_meeting(private_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(teammate_id)
            ahmad.close()


if __name__ == "__main__":
    unittest.main()
