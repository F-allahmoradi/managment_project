"""ابزار MCP برای گرفتن یک مجوز از یک نقش."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import DELETE_ROLE_PERMISSION
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_ROLE_PERMISSION
from services.role_permission import delete_role_permission
from validators.role_permission import validate_delete_role_permission


@run_tool("delete_role_permission")
def run_delete_role_permission(id: int) -> dict:
    """مسیر کامل گرفتن مجوز از نقش را بدون دکوراتور MCP اجرا می‌کند."""
    row_id = validate_delete_role_permission(id)
    deleted_id = delete_role_permission(row_id, actor_id=try_actor_id())
    return format_success("مجوز از نقش گرفته شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_role_permission را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_role_permission,
        name="delete_role_permission",
        title=TITLE_DELETE_ROLE_PERMISSION,
        description=DELETE_ROLE_PERMISSION,
        annotations=DESTRUCTIVE_CRUD,
    )
