"""ابزار MCP برای خواندن یک اقدام تشویق یا تنبیه با شناسه."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_PERFORMANCE_ACTION
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_PERFORMANCE_ACTION
from services.performance_action import fetch_performance_action
from validators.performance_action import validate_get_performance_action


@run_tool("get_performance_action")
def run_get_performance_action(id: int) -> dict:
    """مسیر کامل خواندن اقدام عملکرد را اجرا می‌کند."""
    require_permission("Performance", "Read")
    row_id = validate_get_performance_action(id)
    row = fetch_performance_action(row_id)
    return format_success("اقدام عملکرد خوانده شد", **row)


def register(mcp: MCPServer) -> None:
    """ابزار get_performance_action را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_performance_action,
        name="get_performance_action",
        title=TITLE_GET_PERFORMANCE_ACTION,
        description=GET_PERFORMANCE_ACTION,
        annotations=READ_ONLY_CRUD,
    )
