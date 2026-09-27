"""ابزار MCP برای خواندن یک یادآوری با شناسه.

فقط اگر سازنده، گیرنده، یا عضو فعال پروژه باشید خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.follow_up import require_reminder_access
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_REMINDER
from mcp_server.metadata import READ_ONLY_REMINDER, TITLE_GET_REMINDER
from schemas.input import validate_get_reminder


@logged_tool("get_reminder")
def run_get_reminder(id: int) -> dict:
    """مسیر کامل خواندن یادآوری را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Read")
        reminder_id = validate_get_reminder(id)
        reminder = require_reminder_access(actor["id"], reminder_id)
        return format_success("یادآوری خوانده شد", **reminder)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_reminder را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_reminder",
        title=TITLE_GET_REMINDER,
        description=GET_REMINDER,
        annotations=READ_ONLY_REMINDER,
    )
    def get_reminder(id: int) -> dict:
        """ابزار MCP: یک یادآوری را اگر دسترسی داشته باشید می‌خواند."""
        return run_get_reminder(id=id)
