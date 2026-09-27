"""ابزار MCP برای فهرست گیرنده‌های یک پیام.

فقط اگر عضو گفتگوی همان پیام باشید فهرست برمی‌گردد.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_MESSAGE_RECIPIENTS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_MESSAGE_RECIPIENTS
from services.message import fetch_message_chat_id
from services.message_recipient import fetch_message_recipients
from validators.message_recipient import validate_list_message_recipients


@run_tool("list_message_recipients")
def run_list_message_recipients(
    message_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست گیرنده‌های یک پیام را اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    parsed = validate_list_message_recipients(
        message_id=message_id,
        limit=limit,
        offset=offset,
    )
    chat_id = fetch_message_chat_id(parsed["message_id"])
    require_chat_member(actor["id"], chat_id)
    records = fetch_message_recipients(
        parsed["message_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "گیرنده‌های پیام فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_message_recipients را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_message_recipients",
        title=TITLE_LIST_MESSAGE_RECIPIENTS,
        description=LIST_MESSAGE_RECIPIENTS,
        annotations=READ_ONLY_CRUD,
    )
    def list_message_recipients(
        message_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: ردیف‌های message_recipients یک پیام را می‌خواند."""
        return run_list_message_recipients(
            message_id=message_id,
            limit=limit,
            offset=offset,
        )
