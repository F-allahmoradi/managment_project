"""ابزار MCP برای خواندن یک پیگیری با شناسه از task_follow_ups.

فقط اگر کاربر جاری عضو فعال پروژهٔ همان وظیفه باشد خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_TASK_FOLLOW_UP
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_TASK_FOLLOW_UP
from services.task_follow_up import (
    fetch_task_follow_up,
    fetch_task_follow_up_project_id,
)
from validators.task_follow_up import validate_get_task_follow_up


@run_tool("get_task_follow_up")
def run_get_task_follow_up(id: int) -> dict:
    """مسیر کامل خواندن پیگیری را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("TaskFollowUp", "Read")
    follow_up_id = validate_get_task_follow_up(id)
    project_id = fetch_task_follow_up_project_id(follow_up_id)
    require_active_project_member(actor["id"], project_id)
    follow_up = fetch_task_follow_up(follow_up_id)
    return format_success("پیگیری خوانده شد", **follow_up)


def register(mcp: MCPServer) -> None:
    """ابزار get_task_follow_up را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_task_follow_up,
        name="get_task_follow_up",
        title=TITLE_GET_TASK_FOLLOW_UP,
        description=GET_TASK_FOLLOW_UP,
        annotations=READ_ONLY_CRUD,
    )
