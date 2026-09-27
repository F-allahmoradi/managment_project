"""ابزار MCP برای نرخ تکمیل وظایف."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import task_completion_stats
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_TASK_COMPLETION_STATS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_TASK_COMPLETION_STATS
from mcp_server.scope import actor_for_optional_project


@logged_tool("get_task_completion_stats")
def run_get_task_completion_stats(project_id: Optional[int] = None) -> dict:
    """مسیر کامل نرخ تکمیل وظایف را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Task",
            "Read",
            project_id,
        )
        payload = task_completion_stats(actor["id"], scoped_project)
        return format_success("نرخ تکمیل وظایف محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_task_completion_stats را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_task_completion_stats",
        title=TITLE_GET_TASK_COMPLETION_STATS,
        description=GET_TASK_COMPLETION_STATS,
        annotations=READ_ONLY_STATS,
    )
    def get_task_completion_stats(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: نسبت وظایف تکمیل‌شده را می‌خواند."""
        return run_get_task_completion_stats(project_id=project_id)
