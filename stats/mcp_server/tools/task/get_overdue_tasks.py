"""ابزار MCP برای وظایف گذشته از مهلت در پروژه‌های قابل‌مشاهده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import overdue_tasks
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_OVERDUE_TASKS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_OVERDUE_TASKS
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_optional_project_page


@logged_tool("get_overdue_tasks")
def run_get_overdue_tasks(
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست وظایف عقب‌افتاده را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Task",
            "Read",
            project_id,
        )
        parsed = validate_optional_project_page(
            project_id=scoped_project,
            limit=limit,
            offset=offset,
        )
        records = overdue_tasks(
            actor["id"],
            parsed.get("project_id"),
            parsed["limit"],
            parsed["offset"],
        )
        return format_success(
            "وظایف عقب‌افتاده فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_overdue_tasks را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_overdue_tasks",
        title=TITLE_GET_OVERDUE_TASKS,
        description=GET_OVERDUE_TASKS,
        annotations=READ_ONLY_STATS,
    )
    def get_overdue_tasks(
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: وظایف گذشته از مهلت را می‌خواند."""
        return run_get_overdue_tasks(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
