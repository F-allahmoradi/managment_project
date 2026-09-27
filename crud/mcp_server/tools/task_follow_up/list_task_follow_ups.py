"""ابزار MCP برای فهرست پیگیری‌های یک وظیفه.

فقط اگر کاربر جاری عضو فعال پروژهٔ همان وظیفه باشد فهرست برمی‌گردد.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_TASK_FOLLOW_UPS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_TASK_FOLLOW_UPS
from services.task import fetch_task_project_id
from services.task_follow_up import fetch_task_follow_ups
from validators.task_follow_up import validate_list_task_follow_ups


@run_tool("list_task_follow_ups")
def run_list_task_follow_ups(
    task_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست پیگیری‌های یک وظیفه را اجرا می‌کند."""
    actor = require_permission("TaskFollowUp", "Read")
    parsed = validate_list_task_follow_ups(
        task_id=task_id,
        limit=limit,
        offset=offset,
    )
    project_id = fetch_task_project_id(parsed["task_id"])
    require_active_project_member(actor["id"], project_id)
    records = fetch_task_follow_ups(
        parsed["task_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "پیگیری‌ها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_task_follow_ups را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_task_follow_ups",
        title=TITLE_LIST_TASK_FOLLOW_UPS,
        description=LIST_TASK_FOLLOW_UPS,
        annotations=READ_ONLY_CRUD,
    )
    def list_task_follow_ups(
        task_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: پیگیری‌های task_follow_ups یک وظیفه را می‌خواند."""
        return run_list_task_follow_ups(
            task_id=task_id,
            limit=limit,
            offset=offset,
        )
