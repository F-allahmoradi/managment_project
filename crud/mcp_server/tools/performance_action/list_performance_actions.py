"""ابزار MCP برای فهرست تشویق و تنبیه.

امتیاز و مبلغ ستون جدا هستند. داشبورد رتبه در stats نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_PERFORMANCE_ACTIONS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_PERFORMANCE_ACTIONS
from services.performance_action import fetch_performance_actions
from validators.performance_action import validate_list_performance_actions


@run_tool("list_performance_actions")
def run_list_performance_actions(
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست اقدامات عملکرد را اجرا می‌کند."""
    require_permission("Performance", "Read")
    parsed = validate_list_performance_actions(
        user_id=user_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    records = fetch_performance_actions(
        parsed["limit"],
        parsed["offset"],
        user_id=parsed.get("user_id"),
        project_id=parsed.get("project_id"),
    )
    return format_success(
        "اقدام‌های عملکرد فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_performance_actions را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_performance_actions",
        title=TITLE_LIST_PERFORMANCE_ACTIONS,
        description=LIST_PERFORMANCE_ACTIONS,
        annotations=READ_ONLY_CRUD,
    )
    def list_performance_actions(
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: اقدامات را با امتیاز و مبلغ جدا می‌خواند."""
        return run_list_performance_actions(
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
