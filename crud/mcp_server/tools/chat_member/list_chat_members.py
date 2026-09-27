"""ابزار MCP برای فهرست اعضای یک گفتگو.

فقط اگر خودتان عضو همان گفتگو باشید فهرست برمی‌گردد.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_CHAT_MEMBERS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_CHAT_MEMBERS
from services.chat_member import fetch_chat_members
from validators.chat_member import validate_list_chat_members


@run_tool("list_chat_members")
def run_list_chat_members(
    chat_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست اعضای یک گفتگو را اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    parsed = validate_list_chat_members(
        chat_id=chat_id,
        limit=limit,
        offset=offset,
    )
    require_chat_member(actor["id"], parsed["chat_id"])
    records = fetch_chat_members(
        parsed["chat_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "اعضای گفتگو فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_chat_members را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_chat_members",
        title=TITLE_LIST_CHAT_MEMBERS,
        description=LIST_CHAT_MEMBERS,
        annotations=READ_ONLY_CRUD,
    )
    def list_chat_members(
        chat_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: اعضای chat_members یک گفتگو را می‌خواند."""
        return run_list_chat_members(
            chat_id=chat_id,
            limit=limit,
            offset=offset,
        )
