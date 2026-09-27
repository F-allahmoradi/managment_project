"""ابزار MCP برای شمار ارسال موفق و ناموفق یادآوری."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import delivery_stats
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_DELIVERY_STATS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_DELIVERY_STATS
from mcp_server.scope import actor_for_optional_project


@logged_tool("get_delivery_stats")
def run_get_delivery_stats(project_id: Optional[int] = None) -> dict:
    """مسیر کامل آمار ارسال یادآوری را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Reminder",
            "Read",
            project_id,
        )
        records = delivery_stats(actor["id"], scoped_project)
        return format_success("آمار ارسال یادآوری محاسبه شد", records=records)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_delivery_stats را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_delivery_stats",
        title=TITLE_GET_DELIVERY_STATS,
        description=GET_DELIVERY_STATS,
        annotations=READ_ONLY_STATS,
    )
    def get_delivery_stats(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: شمار SENT و FAILED را از execution_logs می‌خواند."""
        return run_get_delivery_stats(project_id=project_id)
