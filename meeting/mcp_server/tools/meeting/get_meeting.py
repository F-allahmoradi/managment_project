"""ابزار MCP برای خواندن یک جلسه با شناسه."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.meetings import meeting_with_participants, require_meeting_access
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_MEETING
from mcp_server.metadata import READ_ONLY_MEETING, TITLE_GET_MEETING
from validators.meeting import validate_get_meeting


@logged_tool("get_meeting")
def run_get_meeting(id: int) -> dict:
    """مسیر کامل خواندن جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Read")
        meeting_id = validate_get_meeting(id)
        meeting = require_meeting_access(actor["id"], meeting_id)
        payload = meeting_with_participants(meeting)
        return format_success("جلسه خوانده شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_meeting",
        title=TITLE_GET_MEETING,
        description=GET_MEETING,
        annotations=READ_ONLY_MEETING,
    )
    def get_meeting(id: int) -> dict:
        """ابزار MCP: یک جلسه را با شرکت‌کنندگان می‌خواند."""
        return run_get_meeting(id=id)
