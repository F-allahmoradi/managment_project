"""ابزار MCP برای فهرست نقش‌های جدول roles."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from errors.crud import format_success
from mcp_server.docstrings import LIST_ROLES
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_ROLES
from services.role import fetch_roles
from validators.role import validate_list_roles


@run_tool("list_roles")
def run_list_roles(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست نقش‌ها را بدون دکوراتور MCP اجرا می‌کند."""
    parsed_limit, parsed_offset = validate_list_roles(
        limit=limit,
        offset=offset,
    )
    records = fetch_roles(parsed_limit, parsed_offset)
    return format_success(
        "نقش‌ها فهرست شدند",
        records=records,
        limit=parsed_limit,
        offset=parsed_offset,
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_roles را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_roles,
        name="list_roles",
        title=TITLE_LIST_ROLES,
        description=LIST_ROLES,
        annotations=READ_ONLY_CRUD,
    )
