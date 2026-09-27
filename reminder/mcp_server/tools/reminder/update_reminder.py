"""ابزار MCP برای به‌روزرسانی تعریف یک یادآوری.

ارسال رخ نمی‌دهد. گیرنده‌ها دست نمی‌خورند.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.follow_up import (
    require_reminder_access,
    require_reminder_write,
    update_reminder,
)
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import UPDATE_REMINDER
from mcp_server.metadata import TITLE_UPDATE_REMINDER, WRITE_REMINDER
from schemas.input import validate_update_reminder


@logged_tool("update_reminder")
def run_update_reminder(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی تعریف یادآوری را اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Create")
        parsed = validate_update_reminder({"id": id, **fields})
        reminder = require_reminder_access(actor["id"], parsed["id"])
        require_reminder_write(actor["id"], reminder)
        reminder_id = update_reminder(parsed)
        return format_success("یادآوری به‌روزرسانی شد", id=reminder_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار update_reminder را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_reminder",
        title=TITLE_UPDATE_REMINDER,
        description=UPDATE_REMINDER,
        annotations=WRITE_REMINDER,
    )
    def update_reminder_tool(
        id: int,
        title: Optional[str] = None,
        message_template: Optional[str] = None,
        scheduled_at: Optional[str] = None,
        next_run_at: Optional[str] = None,
        reminder_type: Optional[str] = None,
        reminder_type_id: Optional[int] = None,
        frequency: Optional[str] = None,
        frequency_id: Optional[int] = None,
        status: Optional[str] = None,
        status_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: تعریف یادآوری را اگر دسترسی نوشتن داشته باشید عوض می‌کند."""
        return run_update_reminder(
            id=id,
            title=title,
            message_template=message_template,
            scheduled_at=scheduled_at,
            next_run_at=next_run_at,
            reminder_type=reminder_type,
            reminder_type_id=reminder_type_id,
            frequency=frequency,
            frequency_id=frequency_id,
            status=status,
            status_id=status_id,
        )
