"""ابزار MCP برای خواندن یک پیام با شناسه.

فقط اگر کاربر جاری عضو گفتگوی همان پیام باشد خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_MESSAGE
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_MESSAGE
from services.message import fetch_message, fetch_message_chat_id
from validators.message import validate_get_message


@run_tool("get_message")
def run_get_message(id: int) -> dict:
    """مسیر کامل خواندن پیام را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    message_id = validate_get_message(id)
    chat_id = fetch_message_chat_id(message_id)
    require_chat_member(actor["id"], chat_id)
    message = fetch_message(message_id)
    return format_success("پیام خوانده شد", **message)


def register(mcp: MCPServer) -> None:
    """ابزار get_message را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_message,
        name="get_message",
        title=TITLE_GET_MESSAGE,
        description=GET_MESSAGE,
        annotations=READ_ONLY_CRUD,
    )
