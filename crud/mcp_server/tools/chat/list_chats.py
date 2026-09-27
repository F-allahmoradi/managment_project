"""ابزار MCP برای فهرست گفتگوهایی که کاربر جاری عضوشان است."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_CHATS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_CHATS
from services.chat import fetch_chats_for_actor
from validators.chat import validate_list_chats


@run_tool("list_chats")
def run_list_chats(
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست گفتگوهای کاربر جاری را اجرا می‌کند."""
    actor = require_permission("Message", "Read")
    parsed = validate_list_chats(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    if parsed.get("project_id") is not None:
        require_active_project_member(actor["id"], parsed["project_id"])
    records = fetch_chats_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        project_id=parsed.get("project_id"),
    )
    return format_success(
        "گفتگوها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_chats را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_chats",
        title=TITLE_LIST_CHATS,
        description=LIST_CHATS,
        annotations=READ_ONLY_CRUD,
    )
    def list_chats(
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: گفتگوهای عضو بودن را می‌خواند."""
        return run_list_chats(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
