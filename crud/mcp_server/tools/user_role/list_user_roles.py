"""ابزار MCP برای فهرست اتصال‌های کاربر-نقش."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_USER_ROLES
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_USER_ROLES
from services.user_role import fetch_user_roles
from validators.user_role import validate_list_user_roles


@run_tool("list_user_roles")
def run_list_user_roles(
    user_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست نقش‌های کاربر را بدون دکوراتور MCP اجرا می‌کند."""
    require_permission("UserRole", "Read")
    parsed = validate_list_user_roles(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    records = fetch_user_roles(
        parsed["user_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "نقش‌های کاربر فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_user_roles را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_user_roles",
        title=TITLE_LIST_USER_ROLES,
        description=LIST_USER_ROLES,
        annotations=READ_ONLY_CRUD,
    )
    def list_user_roles(
        user_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: اتصال‌های user_roles را می‌خواند."""
        return run_list_user_roles(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
