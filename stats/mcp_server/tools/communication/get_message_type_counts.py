"""ابزار MCP برای شمار پیام‌ها بر اساس نوع."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import message_type_counts
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_MESSAGE_TYPE_COUNTS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_MESSAGE_TYPE_COUNTS
from mcp_server.scope import actor_for_optional_project


@logged_tool("get_message_type_counts")
def run_get_message_type_counts(project_id: Optional[int] = None) -> dict:
    """مسیر کامل شمار نوع پیام را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Message",
            "Read",
            project_id,
        )
        records = message_type_counts(actor["id"], scoped_project)
        return format_success("شمار نوع پیام محاسبه شد", records=records)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_message_type_counts را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_message_type_counts",
        title=TITLE_GET_MESSAGE_TYPE_COUNTS,
        description=GET_MESSAGE_TYPE_COUNTS,
        annotations=READ_ONLY_STATS,
    )
    def get_message_type_counts(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: شمار هشدار و درخواست اقدام را می‌خواند."""
        return run_get_message_type_counts(project_id=project_id)
