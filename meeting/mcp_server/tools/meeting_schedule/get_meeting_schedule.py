"""ابزار MCP برای خواندن یک الگوی جلسه با شناسه."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.schedules import require_schedule_access
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_MEETING_SCHEDULE
from mcp_server.metadata import READ_ONLY_MEETING, TITLE_GET_MEETING_SCHEDULE
from validators.schedule import validate_get_meeting_schedule


@logged_tool("get_meeting_schedule")
def run_get_meeting_schedule(id: int) -> dict:
    """مسیر کامل خواندن الگو را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("MeetingSchedule", "Read")
        schedule_id = validate_get_meeting_schedule(id)
        schedule = require_schedule_access(actor["id"], schedule_id)
        return format_success("الگوی جلسه خوانده شد", **schedule)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_meeting_schedule را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_meeting_schedule",
        title=TITLE_GET_MEETING_SCHEDULE,
        description=GET_MEETING_SCHEDULE,
        annotations=READ_ONLY_MEETING,
    )
    def get_meeting_schedule(id: int) -> dict:
        """ابزار MCP: یک الگو را با شناسه می‌خواند."""
        return run_get_meeting_schedule(id=id)
