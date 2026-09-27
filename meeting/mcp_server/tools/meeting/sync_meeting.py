"""ابزار MCP برای همگام‌سازی خروجی جلسه به پروژه.

NLP استخراج نمی‌کند. متن از contents یا notes است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.sync import sync_meeting
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import SYNC_MEETING
from mcp_server.metadata import TITLE_SYNC_MEETING, WRITE_MEETING
from validators.meeting import validate_sync_meeting


@logged_tool("sync_meeting")
def run_sync_meeting(**fields) -> dict:
    """مسیر کامل همگام‌سازی جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("MeetingSync", "Execute")
        parsed = validate_sync_meeting(fields)
        result = sync_meeting(parsed["id"], parsed, actor_id=actor["id"])
        return format_success("جلسه همگام شد", **result)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار sync_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="sync_meeting",
        title=TITLE_SYNC_MEETING,
        description=SYNC_MEETING,
        annotations=WRITE_MEETING,
    )
    def sync_meeting_tool(
        id: int,
        confirm: bool = False,
        notes: Optional[str] = None,
        decision_title: Optional[str] = None,
        decision_description: Optional[str] = None,
        task_title: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
        task_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        message_text: Optional[str] = None,
        recipient_user_id: Optional[int] = None,
        recipient_external_contact_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: از جلسه وظیفه یا پیام چت پروژه می‌سازد."""
        return run_sync_meeting(
            id=id,
            confirm=confirm,
            notes=notes,
            decision_title=decision_title,
            decision_description=decision_description,
            task_title=task_title,
            assigned_to_user_id=assigned_to_user_id,
            task_id=task_id,
            chat_id=chat_id,
            message_text=message_text,
            recipient_user_id=recipient_user_id,
            recipient_external_contact_id=recipient_external_contact_id,
        )
