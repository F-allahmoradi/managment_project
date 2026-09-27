"""ابزار MCP برای خواندن یک وظیفه با شناسه از tasks.

فقط اگر کاربر جاری عضو فعال پروژهٔ همان وظیفه باشد خوانده می‌شود.
پیگیری‌ها در این پاسخ نیستند.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_TASK
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_TASK
from services.task import fetch_task, fetch_task_project_id
from validators.task import validate_get_task


@run_tool("get_task")
def run_get_task(id: int) -> dict:
    """مسیر کامل خواندن وظیفه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Read")
    task_id = validate_get_task(id)
    project_id = fetch_task_project_id(task_id)
    require_active_project_member(actor["id"], project_id)
    task = fetch_task(task_id)
    return format_success("وظیفه خوانده شد", **task)


def register(mcp: MCPServer) -> None:
    """ابزار get_task را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_task,
        name="get_task",
        title=TITLE_GET_TASK,
        description=GET_TASK,
        annotations=READ_ONLY_CRUD,
    )
