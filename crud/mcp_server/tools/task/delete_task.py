"""ابزار MCP برای حذف یک وظیفه از tasks.

زیرکار و پیگیری با CASCADE پاک می‌شوند. اتصال به موجودیت تحلیل
حذف را رد می‌کند.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_TASK
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_TASK
from services.task import delete_task, fetch_task_project_id
from validators.task import validate_delete_task


@run_tool("delete_task")
def run_delete_task(id: int) -> dict:
    """مسیر کامل حذف وظیفه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Delete")
    task_id = validate_delete_task(id)
    project_id = fetch_task_project_id(task_id)
    require_active_project_member(actor["id"], project_id)
    deleted_id = delete_task(task_id, actor_id=actor["id"])
    return format_success("وظیفه حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_task را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_task,
        name="delete_task",
        title=TITLE_DELETE_TASK,
        description=DELETE_TASK,
        annotations=DESTRUCTIVE_CRUD,
    )
