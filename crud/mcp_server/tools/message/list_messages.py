"""ابزار MCP برای فهرست پیام‌های قابل‌مشاهدهٔ کاربر جاری.

فقط پیام گفتگوهایی برمی‌گردد که کاربر عضوشان است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_MESSAGES
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_MESSAGES
from services.message import fetch_messages_for_actor
from validators.message import validate_list_messages


@run_tool("list_messages")
def run_list_messages(
    chat_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست پیام‌های کاربر جاری را اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    parsed = validate_list_messages(
        chat_id=chat_id,
        limit=limit,
        offset=offset,
    )
    if parsed.get("chat_id") is not None:
        require_chat_member(actor["id"], parsed["chat_id"])
    records = fetch_messages_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        chat_id=parsed.get("chat_id"),
    )
    return format_success(
        "پیام‌ها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_messages را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_messages",
        title=TITLE_LIST_MESSAGES,
        description=LIST_MESSAGES,
        annotations=READ_ONLY_CRUD,
    )
    def list_messages(
        chat_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: پیام گفتگوهای عضو بودن را می‌خواند."""
        return run_list_messages(
            chat_id=chat_id,
            limit=limit,
            offset=offset,
        )
