"""ابزار MCP برای حذف یک نقش غیرسیستمی."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import DELETE_ROLE
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_ROLE
from services.role import delete_role
from validators.role import validate_delete_role


@run_tool("delete_role")
def run_delete_role(id: int) -> dict:
    """مسیر کامل حذف نقش را بدون دکوراتور MCP اجرا می‌کند."""
    role_id = validate_delete_role(id)
    deleted_id = delete_role(role_id, actor_id=try_actor_id())
    return format_success("نقش حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_role را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_role,
        name="delete_role",
        title=TITLE_DELETE_ROLE,
        description=DELETE_ROLE,
        annotations=DESTRUCTIVE_CRUD,
    )
