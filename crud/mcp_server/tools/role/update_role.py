"""ابزار MCP برای به‌روزرسانی یک نقش در roles."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_ROLE
from mcp_server.metadata import TITLE_UPDATE_ROLE, WRITE_CRUD
from services.role import update_role
from validators.role import validate_update_role


@run_tool("update_role")
def run_update_role(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی نقش را بدون دکوراتور MCP اجرا می‌کند."""
    parsed = validate_update_role({"id": id, **fields})
    role_id = update_role(parsed, actor_id=try_actor_id())
    return format_success("نقش به‌روزرسانی شد", id=role_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_role را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_role",
        title=TITLE_UPDATE_ROLE,
        description=UPDATE_ROLE,
        annotations=WRITE_CRUD,
    )
    def update_role_tool(
        id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """ابزار MCP: یک نقش موجود roles را به‌روز می‌کند."""
        return run_update_role(
            id=id,
            name=name,
            description=description,
            is_active=is_active,
        )
