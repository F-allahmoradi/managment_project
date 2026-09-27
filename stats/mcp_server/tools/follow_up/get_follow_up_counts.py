"""ابزار MCP برای شمار پیگیری هر وظیفه."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import follow_up_counts
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_FOLLOW_UP_COUNTS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_FOLLOW_UP_COUNTS
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_follow_up_filter


@logged_tool("get_follow_up_counts")
def run_get_follow_up_counts(
    project_id: Optional[int] = None,
    min_count: int = 0,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل شمار پیگیری وظایف را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "TaskFollowUp",
            "Read",
            project_id,
        )
        parsed = validate_follow_up_filter(
            project_id=scoped_project,
            min_count=min_count,
            limit=limit,
            offset=offset,
        )
        records = follow_up_counts(
            actor["id"],
            parsed.get("project_id"),
            int(parsed.get("min_count") or 0),
            parsed["limit"],
            parsed["offset"],
        )
        return format_success(
            "شمار پیگیری وظایف محاسبه شد",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_follow_up_counts را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_follow_up_counts",
        title=TITLE_GET_FOLLOW_UP_COUNTS,
        description=GET_FOLLOW_UP_COUNTS,
        annotations=READ_ONLY_STATS,
    )
    def get_follow_up_counts(
        project_id: Optional[int] = None,
        min_count: int = 0,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: تعداد پیگیری هر وظیفه را می‌خواند."""
        return run_get_follow_up_counts(
            project_id=project_id,
            min_count=min_count,
            limit=limit,
            offset=offset,
        )
