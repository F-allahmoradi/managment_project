"""ابزار MCP برای خواندن یک گفتگو با شناسه.

فقط اگر کاربر جاری عضو همان گفتگو باشد خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_CHAT
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_CHAT
from services.chat import fetch_chat
from validators.chat import validate_get_chat


@run_tool("get_chat")
def run_get_chat(id: int) -> dict:
    """مسیر کامل خواندن گفتگو را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    chat_id = validate_get_chat(id)
    require_chat_member(actor["id"], chat_id)
    chat = fetch_chat(chat_id)
    return format_success("گفتگو خوانده شد", **chat)


def register(mcp: MCPServer) -> None:
    """ابزار get_chat را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_chat,
        name="get_chat",
        title=TITLE_GET_CHAT,
        description=GET_CHAT,
        annotations=READ_ONLY_CRUD,
    )
