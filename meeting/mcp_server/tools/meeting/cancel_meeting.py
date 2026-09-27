"""ابزار MCP برای لغو جلسه. ردیف حذف نمی‌شود."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.meetings import cancel_meeting
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CANCEL_MEETING
from mcp_server.metadata import TITLE_CANCEL_MEETING, WRITE_MEETING
from validators.meeting import validate_cancel_meeting


@logged_tool("cancel_meeting")
def run_cancel_meeting(id: int) -> dict:
    """مسیر کامل لغو جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Update")
        meeting_id = validate_cancel_meeting(id)
        cancel_meeting(meeting_id, actor_id=actor["id"])
        return format_success("جلسه لغو شد", id=meeting_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار cancel_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="cancel_meeting",
        title=TITLE_CANCEL_MEETING,
        description=CANCEL_MEETING,
        annotations=WRITE_MEETING,
    )
    def cancel_meeting_tool(id: int) -> dict:
        """ابزار MCP: وضعیت جلسه را به لغو شده می‌برد."""
        return run_cancel_meeting(id=id)
