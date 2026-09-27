"""ابزار MCP برای دادن یک نقش به یک کاربر."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_USER_ROLE
from mcp_server.metadata import TITLE_CREATE_USER_ROLE, WRITE_CRUD
from services.user_role import insert_user_role
from validators.user_role import validate_create_user_role


@run_tool("create_user_role")
def run_create_user_role(user_id: int, role_id: int) -> dict:
    """مسیر کامل دادن نقش به کاربر را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("UserRole", "Create")
    parsed = validate_create_user_role(
        {"user_id": user_id, "role_id": role_id}
    )
    new_id = insert_user_role(parsed, actor_id=actor["id"])
    return format_success("نقش به کاربر داده شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_user_role را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_user_role",
        title=TITLE_CREATE_USER_ROLE,
        description=CREATE_USER_ROLE,
        annotations=WRITE_CRUD,
    )
    def create_user_role(user_id: int, role_id: int) -> dict:
        """ابزار MCP: یک ردیف user_roles درج می‌کند."""
        return run_create_user_role(user_id=user_id, role_id=role_id)
