"""ابزار MCP برای چیدن نمونه از روی الگو. تداخل هفتهٔ بعد را پیشنهاد می‌دهد."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.generator import generate_meetings
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GENERATE_MEETINGS
from mcp_server.metadata import TITLE_GENERATE_MEETINGS, WRITE_MEETING
from validators.meeting import validate_generate_meetings


@logged_tool("generate_meetings")
def run_generate_meetings(**fields) -> dict:
    """مسیر کامل تولید نمونه را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Create")
        parsed = validate_generate_meetings(fields)
        result = generate_meetings(
            parsed["schedule_id"],
            actor_id=actor["id"],
            weeks_ahead=parsed.get("weeks_ahead", 1),
            title=parsed.get("title"),
            visibility=parsed.get("visibility"),
        )
        if result.get("created"):
            return format_success("جلسه از روی الگو چیده شد", **result)
        return format_success(
            "این ساعت پر است؛ هفتهٔ بعد پیشنهاد می‌شود",
            **result,
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار generate_meetings را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="generate_meetings",
        title=TITLE_GENERATE_MEETINGS,
        description=GENERATE_MEETINGS,
        annotations=WRITE_MEETING,
    )
    def generate_meetings_tool(
        schedule_id: int,
        weeks_ahead: int = 1,
        title: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: از meeting_schedules یک ردیف meetings می‌سازد."""
        return run_generate_meetings(
            schedule_id=schedule_id,
            weeks_ahead=weeks_ahead,
            title=title,
            visibility=visibility,
        )
