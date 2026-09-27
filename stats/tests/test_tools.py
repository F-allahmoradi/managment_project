"""تست ثبت ابزار آمار و پاکت JSON روی دیتابیس واقعی."""

from datetime import date, timedelta
from pathlib import Path
import asyncio
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import PERMISSION_DENIED, format_error, format_success
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    READ_ONLY_STATS,
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_GET_OVERDUE_TASKS,
    TITLE_GET_PROJECT_PROGRESS,
)
from mcp_server.register import register_stats_tools
from mcp_server.tools.follow_up.get_follow_up_counts import (
    run_get_follow_up_counts,
)
from mcp_server.tools.member.get_member_workload import run_get_member_workload
from mcp_server.tools.project.get_project_health import run_get_project_health
from mcp_server.tools.project.get_project_progress import (
    run_get_project_progress,
)
from mcp_server.tools.project.list_at_risk_projects import (
    run_list_at_risk_projects,
)
from mcp_server.tools.task.get_overdue_tasks import run_get_overdue_tasks
from mcp_server.tools.task.get_task_completion_stats import (
    run_get_task_completion_stats,
)
from mcp_server.tools.task.get_task_status_breakdown import (
    run_get_task_status_breakdown,
)
from services.project import insert_project
from services.task import insert_task
from services.task_follow_up import insert_task_follow_up
from tests.conftest import (
    bind_actor_as_role,
    unique_project_name,
    unique_task_title,
)


_REGISTERED_TOOLS = {
    "get_project_progress",
    "get_project_health",
    "list_at_risk_projects",
    "get_overdue_tasks",
    "get_task_status_breakdown",
    "get_task_completion_stats",
    "get_member_workload",
    "list_members_needing_attention",
    "get_follow_up_counts",
    "get_repeated_follow_ups",
    "get_message_type_counts",
    "get_member_scores",
    "get_performance_dashboard",
    "get_project_costs",
    "get_transaction_summary",
    "get_delivery_stats",
}


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت فقط ابزارهای آمار را بررسی می‌کند."""

    def test_metadata_names_management_stats(self) -> None:
        self.assertEqual(SERVER_NAME, "management-stats")
        self.assertEqual(SERVER_TITLE, "آمار سامانه مدیریت")

    def test_register_adds_stats_tools_only(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_stats_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(names, _REGISTERED_TOOLS)
        self.assertNotIn("create_task", names)
        self.assertNotIn("delete_project", names)

    def test_server_module_lists_registered_tools(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(mcp.name, SERVER_NAME)
        names = {tool.name for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(names, _REGISTERED_TOOLS)

    def test_all_registered_tools_are_read_only(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        progress = by_name["get_project_progress"]
        self.assertEqual(progress.title, TITLE_GET_PROJECT_PROGRESS)
        overdue = by_name["get_overdue_tasks"]
        self.assertEqual(overdue.title, TITLE_GET_OVERDUE_TASKS)
        for tool in tools:
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertEqual(
                tool.annotations.read_only_hint,
                READ_ONLY_STATS.read_only_hint,
            )


class ErrorEnvelopeTests(unittest.TestCase):
    def test_success_envelope(self) -> None:
        payload = format_success("محاسبه شد", task_count=2)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["task_count"], 2)

    def test_unknown_maps_to_database_error(self) -> None:
        payload = format_error(RuntimeError("boom"))
        self.assertEqual(payload["error_code"], "DATABASE_ERROR")


class StatsToolTests(unittest.TestCase):
    """پیشرفت، عقب‌افتادگی، و محدودهٔ عضویت روی Postgres واقعی."""

    def test_progress_overdue_and_outsider_denied(self) -> None:
        owner = bind_actor_as_role("مدیر پروژه")
        outsider = None
        try:
            yesterday = date.today() - timedelta(days=1)
            last_week = yesterday - timedelta(days=6)
            project_id = insert_project(
                {
                    "name": unique_project_name("آمار"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                    "end_date": yesterday.isoformat(),
                    "start_date": last_week.isoformat(),
                },
                created_by=owner.user_id,
            )
            overdue_title = unique_task_title("عقب")
            overdue_id = insert_task(
                {
                    "project_id": project_id,
                    "title": overdue_title,
                    "status": "شروع نشده",
                    "priority": "زیاد",
                    "importance": "زیاد",
                    "assigned_to_user_id": owner.user_id,
                    "start_date": last_week.isoformat(),
                    "due_date": yesterday.isoformat(),
                },
                created_by=owner.user_id,
            )
            insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("تمام"),
                    "status": "تکمیل شده",
                    "priority": "کم",
                    "importance": "کم",
                    "assigned_to_user_id": owner.user_id,
                },
                created_by=owner.user_id,
            )
            insert_task_follow_up(
                {
                    "task_id": overdue_id,
                    "follow_up_type": "تماس",
                    "status": "منتظر پاسخ",
                    "note": "اولین پیگیری آمار",
                },
                followed_by=owner.user_id,
            )

            progress = run_get_project_progress(project_id=project_id)
            self.assertEqual(progress["status"], "success")
            self.assertEqual(progress["task_count"], 2)
            self.assertEqual(progress["completed_count"], 1)
            self.assertEqual(progress["progress_percent"], 50.0)

            completion = run_get_task_completion_stats(project_id=project_id)
            self.assertEqual(completion["status"], "success")
            self.assertEqual(completion["completed_count"], 1)
            self.assertEqual(completion["completion_rate"], 50.0)

            breakdown = run_get_task_status_breakdown(project_id=project_id)
            self.assertEqual(breakdown["status"], "success")
            by_status = {row["status"]: row["count"] for row in breakdown["records"]}
            self.assertEqual(by_status.get("تکمیل شده"), 1)
            self.assertEqual(by_status.get("شروع نشده"), 1)

            overdue = run_get_overdue_tasks(project_id=project_id)
            self.assertEqual(overdue["status"], "success")
            ids = {row["id"] for row in overdue["records"]}
            self.assertIn(overdue_id, ids)
            match = next(row for row in overdue["records"] if row["id"] == overdue_id)
            self.assertEqual(match["title"], overdue_title)
            self.assertGreaterEqual(match["days_overdue"], 1)

            health = run_get_project_health(project_id=project_id)
            self.assertEqual(health["status"], "success")
            self.assertEqual(health["health"], "تأخیر")
            self.assertGreaterEqual(health["overdue_count"], 1)

            at_risk = run_list_at_risk_projects(limit=50, offset=0)
            self.assertEqual(at_risk["status"], "success")
            at_risk_ids = {row["project_id"] for row in at_risk["records"]}
            self.assertIn(project_id, at_risk_ids)

            workload = run_get_member_workload(project_id=project_id)
            self.assertEqual(workload["status"], "success")
            owner_row = next(
                row
                for row in workload["records"]
                if row["user_id"] == owner.user_id
            )
            self.assertGreaterEqual(owner_row["overdue_tasks"], 1)

            follows = run_get_follow_up_counts(project_id=project_id, min_count=1)
            self.assertEqual(follows["status"], "success")
            follow_ids = {row["task_id"] for row in follows["records"]}
            self.assertIn(overdue_id, follow_ids)

            outsider = bind_actor_as_role("کاربر")
            denied = run_get_project_progress(project_id=project_id)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            hidden_overdue = run_get_overdue_tasks(project_id=project_id)
            self.assertEqual(hidden_overdue["status"], "error")
            self.assertEqual(hidden_overdue["error_code"], PERMISSION_DENIED)
            outsider_all = run_get_overdue_tasks()
            self.assertEqual(outsider_all["status"], "success")
            outsider_ids = {row["id"] for row in outsider_all["records"]}
            self.assertNotIn(overdue_id, outsider_ids)
        finally:
            if outsider is not None:
                outsider.close()
            owner.close()


if __name__ == "__main__":
    unittest.main()
