"""ابزار MCP برای دادن یک مجوز به یک نقش."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import CREATE_ROLE_PERMISSION
from mcp_server.metadata import TITLE_CREATE_ROLE_PERMISSION, WRITE_CRUD
from services.role_permission import insert_role_permission
from validators.role_permission import validate_create_role_permission


@run_tool("create_role_permission")
def run_create_role_permission(role_id: int, permission_id: int) -> dict:
    """مسیر کامل دادن مجوز به نقش را بدون دکوراتور MCP اجرا می‌کند."""
    parsed = validate_create_role_permission(
        {"role_id": role_id, "permission_id": permission_id}
    )
    new_id = insert_role_permission(parsed, actor_id=try_actor_id())
    return format_success("مجوز به نقش داده شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_role_permission را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_role_permission",
        title=TITLE_CREATE_ROLE_PERMISSION,
        description=CREATE_ROLE_PERMISSION,
        annotations=WRITE_CRUD,
    )
    def create_role_permission(role_id: int, permission_id: int) -> dict:
        """ابزار MCP: یک ردیف role_permissions درج می‌کند."""
        return run_create_role_permission(
            role_id=role_id,
            permission_id=permission_id,
        )
