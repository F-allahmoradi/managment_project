"""ابزار MCP برای ثبت یک مجوز ریز Resource + Action."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import try_actor_id
from errors.crud import format_success
from mcp_server.docstrings import CREATE_PERMISSION
from mcp_server.metadata import TITLE_CREATE_PERMISSION, WRITE_CRUD
from services.permission import insert_permission
from validators.permission import validate_create_permission


@run_tool("create_permission")
def run_create_permission(**fields) -> dict:
    """مسیر کامل ثبت مجوز را بدون دکوراتور MCP اجرا می‌کند."""
    parsed = validate_create_permission(fields)
    new_id = insert_permission(parsed, actor_id=try_actor_id())
    return format_success("مجوز ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_permission را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_permission",
        title=TITLE_CREATE_PERMISSION,
        description=CREATE_PERMISSION,
        annotations=WRITE_CRUD,
    )
    def create_permission(
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک مجوز ریز در permissions درج می‌کند."""
        return run_create_permission(
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
