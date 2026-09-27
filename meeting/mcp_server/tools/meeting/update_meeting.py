"""ابزار MCP برای به‌روزرسانی جلسه. فقط مدیر همان جلسه."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.meetings import update_meeting
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import UPDATE_MEETING
from mcp_server.metadata import TITLE_UPDATE_MEETING, WRITE_MEETING
from validators.meeting import validate_update_meeting


@logged_tool("update_meeting")
def run_update_meeting(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Update")
        parsed = validate_update_meeting({"id": id, **fields})
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        meeting_id = update_meeting(parsed, actor_id=actor["id"])
        return format_success("جلسه به‌روزرسانی شد", id=meeting_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار update_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_meeting",
        title=TITLE_UPDATE_MEETING,
        description=UPDATE_MEETING,
        annotations=WRITE_MEETING,
    )
    def update_meeting_tool(
        id: int,
        title: Optional[str] = None,
        scheduled_at: Optional[str] = None,
        meeting_type: Optional[str] = None,
        meeting_type_id: Optional[int] = None,
        duration_minutes: Optional[int] = None,
        project_id: Optional[int] = None,
        visibility: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: جلسهٔ موجود را اگر مدیرش باشید به‌روز می‌کند."""
        return run_update_meeting(
            id=id,
            title=title,
            scheduled_at=scheduled_at,
            meeting_type=meeting_type,
            meeting_type_id=meeting_type_id,
            duration_minutes=duration_minutes,
            project_id=project_id,
            visibility=visibility,
            location=location,
        )
