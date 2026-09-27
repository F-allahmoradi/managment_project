"""ابزار MCP برای وضعیت کلی و برچسب سلامت یک پروژه."""

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import project_health
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_PROJECT_HEALTH
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_PROJECT_HEALTH
from mcp_server.scope import actor_for_project


@logged_tool("get_project_health")
def run_get_project_health(project_id: int) -> dict:
    """مسیر کامل سلامت پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        _actor, parsed = actor_for_project("Project", "Read", project_id)
        payload = project_health(parsed)
        return format_success("سلامت پروژه محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_project_health را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_project_health",
        title=TITLE_GET_PROJECT_HEALTH,
        description=GET_PROJECT_HEALTH,
        annotations=READ_ONLY_STATS,
    )
    def get_project_health(project_id: int) -> dict:
        """ابزار MCP: درصد و برچسب سلامت یک پروژه را می‌خواند."""
        return run_get_project_health(project_id=project_id)
