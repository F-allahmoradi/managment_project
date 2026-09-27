"""ابزار MCP برای فهرست اعلان‌های خود کاربر جاری.

اعلان دیگران در این فهرست نیست. نوع از seed است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_actor
from errors.crud import format_success
from mcp_server.docstrings import LIST_NOTIFICATIONS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_NOTIFICATIONS
from services.notification import fetch_notifications_for_actor
from validators.notification import validate_list_notifications


@run_tool("list_notifications")
def run_list_notifications(
    is_read: Optional[bool] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست اعلان‌های کاربر جاری را اجرا می‌کند."""
    actor = require_active_actor()
    parsed = validate_list_notifications(
        is_read=is_read,
        limit=limit,
        offset=offset,
    )
    records = fetch_notifications_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        is_read=parsed.get("is_read"),
    )
    return format_success(
        "اعلان‌ها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_notifications را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_notifications",
        title=TITLE_LIST_NOTIFICATIONS,
        description=LIST_NOTIFICATIONS,
        annotations=READ_ONLY_CRUD,
    )
    def list_notifications(
        is_read: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: فقط اعلان‌های خود کاربر جاری را می‌خواند."""
        return run_list_notifications(
            is_read=is_read,
            limit=limit,
            offset=offset,
        )
