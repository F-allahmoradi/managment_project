"""ابزار MCP برای فهرست وظایف قابل‌مشاهدهٔ کاربر جاری.

فقط وظایف پروژه‌هایی برمی‌گردد که کاربر عضو فعال‌شان است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_TASKS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_TASKS
from services.task import fetch_tasks_for_actor
from validators.task import validate_list_tasks


@run_tool("list_tasks")
def run_list_tasks(
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست وظایف کاربر جاری را اجرا می‌کند."""
    actor = require_permission("Task", "Read")
    parsed = validate_list_tasks(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    if parsed.get("project_id") is not None:
        require_active_project_member(actor["id"], parsed["project_id"])
    records = fetch_tasks_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        project_id=parsed.get("project_id"),
    )
    return format_success(
        "وظیفه‌ها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_tasks را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_tasks",
        title=TITLE_LIST_TASKS,
        description=LIST_TASKS,
        annotations=READ_ONLY_CRUD,
    )
    def list_tasks(
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: وظایف پروژه‌های عضو فعال بودن را می‌خواند."""
        return run_list_tasks(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
