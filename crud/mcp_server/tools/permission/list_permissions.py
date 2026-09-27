"""ابزار MCP برای فهرست مجوزهای جدول permissions."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from errors.crud import format_success
from mcp_server.docstrings import LIST_PERMISSIONS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_PERMISSIONS
from services.permission import fetch_permissions
from validators.permission import validate_list_permissions


@run_tool("list_permissions")
def run_list_permissions(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست مجوزها را بدون دکوراتور MCP اجرا می‌کند."""
    parsed_limit, parsed_offset = validate_list_permissions(
        limit=limit,
        offset=offset,
    )
    records = fetch_permissions(parsed_limit, parsed_offset)
    return format_success(
        "مجوزها فهرست شدند",
        records=records,
        limit=parsed_limit,
        offset=parsed_offset,
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_permissions را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_permissions,
        name="list_permissions",
        title=TITLE_LIST_PERMISSIONS,
        description=LIST_PERMISSIONS,
        annotations=READ_ONLY_CRUD,
    )
