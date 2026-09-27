"""ابزار MCP برای دیدن وضعیت پیگیری هر گیرندهٔ یک یادآوری."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.follow_up import (
    fetch_follow_up_states,
    require_reminder_access,
)
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_FOLLOW_UP_STATES
from mcp_server.metadata import READ_ONLY_REMINDER, TITLE_LIST_FOLLOW_UP_STATES
from schemas.input import validate_list_follow_up_states


@logged_tool("list_follow_up_states")
def run_list_follow_up_states(
    reminder_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست وضعیت پیگیری گیرنده‌ها را اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Read")
        parsed = validate_list_follow_up_states(
            reminder_id=reminder_id,
            limit=limit,
            offset=offset,
        )
        require_reminder_access(actor["id"], parsed["reminder_id"])
        records = fetch_follow_up_states(
            parsed["reminder_id"],
            parsed["limit"],
            parsed["offset"],
        )
        return format_success(
            "وضعیت پیگیری گیرنده‌ها فهرست شد",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_follow_up_states را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_follow_up_states",
        title=TITLE_LIST_FOLLOW_UP_STATES,
        description=LIST_FOLLOW_UP_STATES,
        annotations=READ_ONLY_REMINDER,
    )
    def list_follow_up_states(
        reminder_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: follow_up_states یک یادآوری را می‌خواند."""
        return run_list_follow_up_states(
            reminder_id=reminder_id,
            limit=limit,
            offset=offset,
        )
