"""ابزار MCP برای ساخت گفتگو؛ خصوصی یا روی پروژه.

سازنده همان لحظه عضو chat_members می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_CHAT
from mcp_server.metadata import TITLE_CREATE_CHAT, WRITE_CRUD
from services.chat import insert_chat
from validators.chat import validate_create_chat


@run_tool("create_chat")
def run_create_chat(**fields) -> dict:
    """مسیر کامل ساخت گفتگو را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Create")
    parsed = validate_create_chat(fields)
    if parsed.get("project_id") is not None:
        require_active_project_member(actor["id"], parsed["project_id"])
    new_id = insert_chat(parsed, created_by=actor["id"])
    return format_success("گفتگو ساخته شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_chat را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_chat",
        title=TITLE_CREATE_CHAT,
        description=CREATE_CHAT,
        annotations=WRITE_CRUD,
    )
    def create_chat(
        title: str,
        chat_type: Optional[str] = None,
        chat_type_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف chats درج می‌کند و سازنده را عضو می‌کند."""
        return run_create_chat(
            title=title,
            chat_type=chat_type,
            chat_type_id=chat_type_id,
            project_id=project_id,
        )
