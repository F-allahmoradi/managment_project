"""ابزار MCP برای فهرست الگوهای جلسهٔ کاربر جاری."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.schedules import fetch_schedules
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_MEETING_SCHEDULES
from mcp_server.metadata import READ_ONLY_MEETING, TITLE_LIST_MEETING_SCHEDULES
from validators.schedule import validate_list_meeting_schedules


@logged_tool("list_meeting_schedules")
def run_list_meeting_schedules(
    project_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست الگوها را اجرا می‌کند."""
    try:
        actor = require_permission("MeetingSchedule", "Read")
        parsed = validate_list_meeting_schedules(
            project_id=project_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        records = fetch_schedules(
            actor["id"],
            parsed["limit"],
            parsed["offset"],
            project_id=parsed.get("project_id"),
            is_active=parsed.get("is_active"),
        )
        return format_success(
            "الگوهای جلسه فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_meeting_schedules را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_meeting_schedules",
        title=TITLE_LIST_MEETING_SCHEDULES,
        description=LIST_MEETING_SCHEDULES,
        annotations=READ_ONLY_MEETING,
    )
    def list_meeting_schedules(
        project_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: الگوهای جلسهٔ کاربر جاری را می‌خواند."""
        return run_list_meeting_schedules(
            project_id=project_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
