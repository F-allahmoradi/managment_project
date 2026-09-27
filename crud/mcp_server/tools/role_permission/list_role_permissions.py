"""ابزار MCP برای فهرست اتصال‌های نقش-مجوز."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from errors.crud import format_success
from mcp_server.docstrings import LIST_ROLE_PERMISSIONS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_ROLE_PERMISSIONS
from services.role_permission import fetch_role_permissions
from validators.role_permission import validate_list_role_permissions


@run_tool("list_role_permissions")
def run_list_role_permissions(
    role_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست مجوزهای نقش را بدون دکوراتور MCP اجرا می‌کند."""
    parsed = validate_list_role_permissions(
        role_id=role_id,
        limit=limit,
        offset=offset,
    )
    records = fetch_role_permissions(
        parsed["role_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "مجوزهای نقش فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_role_permissions را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_role_permissions",
        title=TITLE_LIST_ROLE_PERMISSIONS,
        description=LIST_ROLE_PERMISSIONS,
        annotations=READ_ONLY_CRUD,
    )
    def list_role_permissions(
        role_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: اتصال‌های role_permissions را می‌خواند."""
        return run_list_role_permissions(
            role_id=role_id,
            limit=limit,
            offset=offset,
        )
