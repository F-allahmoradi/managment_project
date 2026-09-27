"""ابزار MCP برای فهرست یادآوری‌های قابل‌مشاهدهٔ کاربر جاری."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.follow_up import fetch_reminders_for_actor
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_REMINDERS
from mcp_server.metadata import READ_ONLY_REMINDER, TITLE_LIST_REMINDERS
from schemas.input import validate_list_reminders


@logged_tool("list_reminders")
def run_list_reminders(
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست یادآوری‌های کاربر جاری را اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Read")
        parsed = validate_list_reminders(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        records = fetch_reminders_for_actor(
            actor["id"],
            parsed["limit"],
            parsed["offset"],
            project_id=parsed.get("project_id"),
        )
        return format_success(
            "یادآوری‌ها فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_reminders را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_reminders",
        title=TITLE_LIST_REMINDERS,
        description=LIST_REMINDERS,
        annotations=READ_ONLY_REMINDER,
    )
    def list_reminders(
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: یادآوری‌های قابل‌مشاهده را می‌خواند."""
        return run_list_reminders(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
