"""ابزار MCP برای خواندن یک محتوا با شناسه از contents."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_CONTENT
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_CONTENT
from services.content import fetch_content
from validators.content import validate_get_content


@run_tool("get_content")
def run_get_content(id: int) -> dict:
    """مسیر کامل خواندن محتوا را بدون دکوراتور MCP اجرا می‌کند."""
    require_permission("Content", "Read")
    content_id = validate_get_content(id)
    row = fetch_content(content_id)
    return format_success("محتوا خوانده شد", **row)


def register(mcp: MCPServer) -> None:
    """ابزار get_content را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_content,
        name="get_content",
        title=TITLE_GET_CONTENT,
        description=GET_CONTENT,
        annotations=READ_ONLY_CRUD,
    )
