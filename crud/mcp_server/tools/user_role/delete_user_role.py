"""ابزار MCP برای گرفتن یک نقش از یک کاربر."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_USER_ROLE
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_USER_ROLE
from services.user_role import delete_user_role
from validators.user_role import validate_delete_user_role


@run_tool("delete_user_role")
def run_delete_user_role(id: int) -> dict:
    """مسیر کامل گرفتن نقش از کاربر را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("UserRole", "Delete")
    row_id = validate_delete_user_role(id)
    deleted_id = delete_user_role(row_id, actor_id=actor["id"])
    return format_success("نقش از کاربر گرفته شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_user_role را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_user_role,
        name="delete_user_role",
        title=TITLE_DELETE_USER_ROLE,
        description=DELETE_USER_ROLE,
        annotations=DESTRUCTIVE_CRUD,
    )
