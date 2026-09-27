"""ابزار MCP برای اعضای دارای وظیفهٔ عقب‌افتاده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import members_needing_attention
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_MEMBERS_NEEDING_ATTENTION
from mcp_server.metadata import (
    READ_ONLY_STATS,
    TITLE_LIST_MEMBERS_NEEDING_ATTENTION,
)
from mcp_server.scope import actor_for_optional_project


@logged_tool("list_members_needing_attention")
def run_list_members_needing_attention(project_id: Optional[int] = None) -> dict:
    """مسیر کامل فهرست اعضای نیازمند پیگیری را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Task",
            "Read",
            project_id,
        )
        records = members_needing_attention(actor["id"], scoped_project)
        return format_success(
            "اعضای نیازمند پیگیری فهرست شدند",
            records=records,
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_members_needing_attention را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_members_needing_attention",
        title=TITLE_LIST_MEMBERS_NEEDING_ATTENTION,
        description=LIST_MEMBERS_NEEDING_ATTENTION,
        annotations=READ_ONLY_STATS,
    )
    def list_members_needing_attention(project_id: Optional[int] = None) -> dict:
        """ابزار MCP: اعضای با وظیفهٔ عقب‌افتاده را می‌خواند."""
        return run_list_members_needing_attention(project_id=project_id)
