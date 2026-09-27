"""ابزار MCP برای فهرست جلسات قابل‌مشاهده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_project_member, require_permission
from business_logic.meetings import fetch_meetings
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_MEETINGS
from mcp_server.metadata import READ_ONLY_MEETING, TITLE_LIST_MEETINGS
from validators.meeting import validate_list_meetings


@logged_tool("list_meetings")
def run_list_meetings(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    status_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست جلسات را اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Read")
        parsed = validate_list_meetings(
            project_id=project_id,
            status=status,
            status_id=status_id,
            limit=limit,
            offset=offset,
        )
        if parsed.get("project_id") is not None:
            require_active_project_member(actor["id"], parsed["project_id"])
        records = fetch_meetings(
            actor["id"],
            parsed["limit"],
            parsed["offset"],
            project_id=parsed.get("project_id"),
            status_id=parsed.get("status_id"),
            status=parsed.get("status"),
        )
        return format_success(
            "جلسات فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_meetings را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_meetings",
        title=TITLE_LIST_MEETINGS,
        description=LIST_MEETINGS,
        annotations=READ_ONLY_MEETING,
    )
    def list_meetings(
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        status_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: جلسات قابل‌مشاهده را می‌خواند."""
        return run_list_meetings(
            project_id=project_id,
            status=status,
            status_id=status_id,
            limit=limit,
            offset=offset,
        )
