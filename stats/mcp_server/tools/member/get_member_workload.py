"""ابزار MCP برای بار کاری اعضای پروژه‌های قابل‌مشاهده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import member_workload
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_MEMBER_WORKLOAD
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_MEMBER_WORKLOAD
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_member_filter


@logged_tool("get_member_workload")
def run_get_member_workload(
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> dict:
    """مسیر کامل بار کاری اعضا را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Task",
            "Read",
            project_id,
        )
        parsed = validate_member_filter(
            project_id=scoped_project,
            user_id=user_id,
        )
        records = member_workload(
            actor["id"],
            parsed.get("project_id"),
            parsed.get("user_id"),
        )
        return format_success("بار کاری اعضا محاسبه شد", records=records)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_member_workload را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_member_workload",
        title=TITLE_GET_MEMBER_WORKLOAD,
        description=GET_MEMBER_WORKLOAD,
        annotations=READ_ONLY_STATS,
    )
    def get_member_workload(
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: شمار وظایف باز و عقب‌افتادهٔ هر عضو را می‌خواند."""
        return run_get_member_workload(project_id=project_id, user_id=user_id)
