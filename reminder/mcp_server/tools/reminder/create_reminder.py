"""ابزار MCP برای تعریف یادآوری با گیرنده و وضعیت پیگیری اولیه.

content_id و task_item_id نوشته نمی‌شوند. ارسال با send_reminder است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.follow_up import insert_reminder
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_REMINDER
from mcp_server.metadata import TITLE_CREATE_REMINDER, WRITE_REMINDER
from schemas.input import validate_create_reminder


@logged_tool("create_reminder")
def run_create_reminder(**fields) -> dict:
    """مسیر کامل تعریف یادآوری را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Create")
        parsed = validate_create_reminder(fields)
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        new_id = insert_reminder(parsed, created_by=actor["id"])
        return format_success("یادآوری ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_reminder را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_reminder",
        title=TITLE_CREATE_REMINDER,
        description=CREATE_REMINDER,
        annotations=WRITE_REMINDER,
    )
    def create_reminder(
        title: str,
        message_template: str,
        scheduled_at: str,
        reminder_type: Optional[str] = None,
        reminder_type_id: Optional[int] = None,
        frequency: Optional[str] = None,
        frequency_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        target_external_contact_id: Optional[int] = None,
        project_id: Optional[int] = None,
        next_run_at: Optional[str] = None,
        status: Optional[str] = None,
        status_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: reminders و گیرنده‌ها و follow_up_states را درج می‌کند."""
        return run_create_reminder(
            title=title,
            message_template=message_template,
            scheduled_at=scheduled_at,
            reminder_type=reminder_type,
            reminder_type_id=reminder_type_id,
            frequency=frequency,
            frequency_id=frequency_id,
            target_user_id=target_user_id,
            target_external_contact_id=target_external_contact_id,
            project_id=project_id,
            next_run_at=next_run_at,
            status=status,
            status_id=status_id,
        )
