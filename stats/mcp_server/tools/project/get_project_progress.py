"""ابزار MCP برای درصد پیشرفت یک پروژه از وضعیت وظایف."""

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import project_progress
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_PROJECT_PROGRESS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_PROJECT_PROGRESS
from mcp_server.scope import actor_for_project


@logged_tool("get_project_progress")
def run_get_project_progress(project_id: int) -> dict:
    """مسیر کامل پیشرفت پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        _actor, parsed = actor_for_project("Project", "Read", project_id)
        payload = project_progress(parsed)
        return format_success("پیشرفت پروژه محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_project_progress را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_project_progress",
        title=TITLE_GET_PROJECT_PROGRESS,
        description=GET_PROJECT_PROGRESS,
        annotations=READ_ONLY_STATS,
    )
    def get_project_progress(project_id: int) -> dict:
        """ابزار MCP: درصد وظایف تکمیل‌شدهٔ یک پروژه را می‌خواند."""
        return run_get_project_progress(project_id=project_id)
