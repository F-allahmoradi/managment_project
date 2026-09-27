"""ابزار MCP برای ساخت الگوی تکرار جلسه."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.schedules import insert_schedule
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_MEETING_SCHEDULE
from mcp_server.metadata import TITLE_CREATE_MEETING_SCHEDULE, WRITE_MEETING
from validators.schedule import validate_create_meeting_schedule


@logged_tool("create_meeting_schedule")
def run_create_meeting_schedule(**fields) -> dict:
    """مسیر کامل ساخت الگو را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("MeetingSchedule", "Create")
        parsed = validate_create_meeting_schedule(fields)
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        new_id = insert_schedule(parsed, user_id=actor["id"])
        return format_success("الگوی جلسه ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_meeting_schedule را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_meeting_schedule",
        title=TITLE_CREATE_MEETING_SCHEDULE,
        description=CREATE_MEETING_SCHEDULE,
        annotations=WRITE_MEETING,
    )
    def create_meeting_schedule(
        start_time: str,
        meeting_type: Optional[str] = None,
        meeting_type_id: Optional[int] = None,
        day_of_week: Optional[int] = None,
        day_name: Optional[str] = None,
        duration_minutes: int = 60,
        project_id: Optional[int] = None,
        is_active: bool = True,
        effective_from: Optional[str] = None,
        effective_until: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف meeting_schedules درج می‌کند."""
        return run_create_meeting_schedule(
            start_time=start_time,
            meeting_type=meeting_type,
            meeting_type_id=meeting_type_id,
            day_of_week=day_of_week,
            day_name=day_name,
            duration_minutes=duration_minutes,
            project_id=project_id,
            is_active=is_active,
            effective_from=effective_from,
            effective_until=effective_until,
        )
