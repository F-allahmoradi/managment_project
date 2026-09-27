"""ابزار MCP برای امتیاز و شمار تشویق/تنبیه اعضا."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import member_scores
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_MEMBER_SCORES
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_MEMBER_SCORES
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_member_filter


@logged_tool("get_member_scores")
def run_get_member_scores(
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> dict:
    """مسیر کامل امتیاز اعضا را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Performance",
            "Read",
            project_id,
        )
        parsed = validate_member_filter(
            project_id=scoped_project,
            user_id=user_id,
        )
        records = member_scores(
            actor["id"],
            parsed.get("project_id"),
            parsed.get("user_id"),
        )
        return format_success("امتیاز اعضا محاسبه شد", records=records)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_member_scores را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_member_scores",
        title=TITLE_GET_MEMBER_SCORES,
        description=GET_MEMBER_SCORES,
        annotations=READ_ONLY_STATS,
    )
    def get_member_scores(
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: جمع امتیاز هر عضو را می‌خواند."""
        return run_get_member_scores(project_id=project_id, user_id=user_id)
