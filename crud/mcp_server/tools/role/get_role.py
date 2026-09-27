"""ابزار MCP برای خواندن یک نقش با شناسه."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from errors.crud import format_success
from mcp_server.docstrings import GET_ROLE
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_ROLE
from services.role import fetch_role
from validators.role import validate_get_role


@run_tool("get_role")
def run_get_role(id: int) -> dict:
    """مسیر کامل خواندن نقش را بدون دکوراتور MCP اجرا می‌کند."""
    role_id = validate_get_role(id)
    role = fetch_role(role_id)
    return format_success("نقش خوانده شد", **role)


def register(mcp: MCPServer) -> None:
    """ابزار get_role را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_role,
        name="get_role",
        title=TITLE_GET_ROLE,
        description=GET_ROLE,
        annotations=READ_ONLY_CRUD,
    )
