"""ابزار MCP برای خلاصهٔ تشویق و تنبیه محدوده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import performance_dashboard
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_PERFORMANCE_DASHBOARD
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_PERFORMANCE_DASHBOARD
from mcp_server.scope import actor_for_optional_project


@logged_tool("get_performance_dashboard")
def run_get_performance_dashboard(project_id: Optional[int] = None) -> dict:
    """مسیر کامل داشبورد عملکرد را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Performance",
            "Read",
            project_id,
        )
        payload = performance_dashboard(actor["id"], scoped_project)
        return format_success("داشبورد عملکرد محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_performance_dashboard را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_performance_dashboard",
        title=TITLE_GET_PERFORMANCE_DASHBOARD,
        description=GET_PERFORMANCE_DASHBOARD,
        annotations=READ_ONLY_STATS,
    )
    def get_performance_dashboard(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: خلاصهٔ تشویق و تنبیه را می‌خواند."""
        return run_get_performance_dashboard(project_id=project_id)
