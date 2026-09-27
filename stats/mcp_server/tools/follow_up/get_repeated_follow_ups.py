"""ابزار MCP برای وظایف با پیگیری تکراری بالاتر از آستانه."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import repeated_follow_ups
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_REPEATED_FOLLOW_UPS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_REPEATED_FOLLOW_UPS
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_follow_up_filter


@logged_tool("get_repeated_follow_ups")
def run_get_repeated_follow_ups(
    project_id: Optional[int] = None,
    min_count: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل پیگیری‌های تکراری را اجرا می‌کند."""
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
        records = repeated_follow_ups(
            actor["id"],
            parsed.get("project_id"),
            parsed.get("min_count"),
            parsed["limit"],
            parsed["offset"],
        )
        return format_success(
            "پیگیری‌های تکراری فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_repeated_follow_ups را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_repeated_follow_ups",
        title=TITLE_GET_REPEATED_FOLLOW_UPS,
        description=GET_REPEATED_FOLLOW_UPS,
        annotations=READ_ONLY_STATS,
    )
    def get_repeated_follow_ups(
        project_id: Optional[int] = None,
        min_count: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: وظایف با پیگیری زیاد را می‌خواند."""
        return run_get_repeated_follow_ups(
            project_id=project_id,
            min_count=min_count,
            limit=limit,
            offset=offset,
        )
