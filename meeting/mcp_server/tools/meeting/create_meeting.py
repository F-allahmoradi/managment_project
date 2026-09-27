"""ابزار MCP برای ساخت یک جلسه مشخص. ضبط نوشته نمی‌شود."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.meetings import insert_meeting
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_MEETING
from mcp_server.metadata import TITLE_CREATE_MEETING, WRITE_MEETING
from validators.meeting import validate_create_meeting


@logged_tool("create_meeting")
def run_create_meeting(**fields) -> dict:
    """مسیر کامل ساخت جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Create")
        parsed = validate_create_meeting(fields)
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        new_id = insert_meeting(parsed, manager_user_id=actor["id"])
        return format_success("جلسه ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_meeting",
        title=TITLE_CREATE_MEETING,
        description=CREATE_MEETING,
        annotations=WRITE_MEETING,
    )
    def create_meeting(
        title: str,
        scheduled_at: str,
        meeting_type: Optional[str] = None,
        meeting_type_id: Optional[int] = None,
        duration_minutes: int = 60,
        project_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        visibility: str = "PRIVATE",
        location: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف meetings درج می‌کند."""
        return run_create_meeting(
            title=title,
            scheduled_at=scheduled_at,
            meeting_type=meeting_type,
            meeting_type_id=meeting_type_id,
            duration_minutes=duration_minutes,
            project_id=project_id,
            schedule_id=schedule_id,
            visibility=visibility,
            location=location,
        )
