"""ابزار MCP برای جمع هزینه و دریافت یک پروژه."""

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import project_costs
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_PROJECT_COSTS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_PROJECT_COSTS
from mcp_server.scope import actor_for_project


@logged_tool("get_project_costs")
def run_get_project_costs(project_id: int) -> dict:
    """مسیر کامل هزینهٔ پروژه را اجرا می‌کند."""
    try:
        _actor, parsed = actor_for_project("Finance", "Read", project_id)
        payload = project_costs(parsed)
        return format_success("هزینه پروژه محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_project_costs را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_project_costs",
        title=TITLE_GET_PROJECT_COSTS,
        description=GET_PROJECT_COSTS,
        annotations=READ_ONLY_STATS,
    )
    def get_project_costs(project_id: int) -> dict:
        """ابزار MCP: جمع تراکنش‌های یک پروژه را می‌خواند."""
        return run_get_project_costs(project_id=project_id)
