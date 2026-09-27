"""ابزار MCP برای ثبت یک نقش جدید در roles.

نقش سیستمی ساخته نمی‌شود؛ seed دست‌نخورده می‌ماند.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import CREATE_ROLE
from mcp_server.metadata import TITLE_CREATE_ROLE, WRITE_CRUD
from services.role import insert_role
from validators.role import validate_create_role


@run_tool("create_role")
def run_create_role(**fields) -> dict:
    """مسیر کامل ثبت نقش را بدون دکوراتور MCP اجرا می‌کند."""
    parsed = validate_create_role(fields)
    new_id = insert_role(parsed, actor_id=try_actor_id())
    return format_success("نقش ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_role را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_role",
        title=TITLE_CREATE_ROLE,
        description=CREATE_ROLE,
        annotations=WRITE_CRUD,
    )
    def create_role(
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> dict:
        """ابزار MCP: یک نقش غیرسیستمی در roles درج می‌کند."""
        return run_create_role(
            name=name,
            description=description,
            is_active=is_active,
        )
