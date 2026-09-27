"""ابزار MCP برای افزودن کاربر سامانه به یک گفتگو.

مخاطب خارجی عضو chat_members نمی‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_CHAT_MEMBER
from mcp_server.metadata import TITLE_CREATE_CHAT_MEMBER, WRITE_CRUD
from services.chat_member import insert_chat_member
from validators.chat_member import validate_create_chat_member


@run_tool("create_chat_member")
def run_create_chat_member(chat_id: int, user_id: int) -> dict:
    """مسیر کامل افزودن عضو گفتگو را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Create")
    parsed = validate_create_chat_member(
        {"chat_id": chat_id, "user_id": user_id}
    )
    require_chat_member(actor["id"], parsed["chat_id"])
    new_id = insert_chat_member(parsed, actor_id=actor["id"])
    return format_success("عضو به گفتگو اضافه شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_chat_member را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_chat_member",
        title=TITLE_CREATE_CHAT_MEMBER,
        description=CREATE_CHAT_MEMBER,
        annotations=WRITE_CRUD,
    )
    def create_chat_member(chat_id: int, user_id: int) -> dict:
        """ابزار MCP: یک ردیف chat_members برای کاربر سامانه درج می‌کند."""
        return run_create_chat_member(chat_id=chat_id, user_id=user_id)
