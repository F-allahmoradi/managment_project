"""ابزار MCP برای وصل کردن ضبط به جلسه. محتوا از crud می‌آید."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.record import record_meeting
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import RECORD_MEETING
from mcp_server.metadata import TITLE_RECORD_MEETING, WRITE_MEETING
from validators.meeting import validate_record_meeting


@logged_tool("record_meeting")
def run_record_meeting(id: int, content_id: int) -> dict:
    """مسیر کامل ضبط جلسه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Update")
        parsed = validate_record_meeting({"id": id, "content_id": content_id})
        record_meeting(parsed["id"], parsed["content_id"], actor_id=actor["id"])
        return format_success("جلسه ضبط شد", id=parsed["id"], content_id=parsed["content_id"])
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار record_meeting را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="record_meeting",
        title=TITLE_RECORD_MEETING,
        description=RECORD_MEETING,
        annotations=WRITE_MEETING,
    )
    def record_meeting_tool(id: int, content_id: int) -> dict:
        """ابزار MCP: content_id را به جلسه وصل می‌کند؛ وضعیت ضبط شده می‌شود."""
        return run_record_meeting(id=id, content_id=content_id)
