"""ابزار MCP برای توزیع وضعیت وظایف."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import task_status_breakdown
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_TASK_STATUS_BREAKDOWN
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_TASK_STATUS_BREAKDOWN
from mcp_server.scope import actor_for_optional_project


@logged_tool("get_task_status_breakdown")
def run_get_task_status_breakdown(project_id: Optional[int] = None) -> dict:
    """مسیر کامل توزیع وضعیت وظایف را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Task",
            "Read",
            project_id,
        )
        records = task_status_breakdown(actor["id"], scoped_project)
        return format_success("توزیع وضعیت وظایف محاسبه شد", records=records)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_task_status_breakdown را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_task_status_breakdown",
        title=TITLE_GET_TASK_STATUS_BREAKDOWN,
        description=GET_TASK_STATUS_BREAKDOWN,
        annotations=READ_ONLY_STATS,
    )
    def get_task_status_breakdown(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: شمار وظایف هر وضعیت را می‌خواند."""
        return run_get_task_status_breakdown(project_id=project_id)
