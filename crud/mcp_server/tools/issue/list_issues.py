"""ابزار MCP برای فهرست مسائل قابل‌مشاهدهٔ کاربر جاری.

فقط مسائل پروژه‌هایی برمی‌گردد که کاربر عضو فعال‌شان است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_ISSUES
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_ISSUES
from services.issue import fetch_issues_for_actor
from validators.issue import validate_list_issues


@run_tool("list_issues")
def run_list_issues(
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست مسائل کاربر جاری را اجرا می‌کند."""
    actor = require_permission("Issue", "Read")
    parsed = validate_list_issues(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    if parsed.get("project_id") is not None:
        require_active_project_member(actor["id"], parsed["project_id"])
    records = fetch_issues_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        project_id=parsed.get("project_id"),
    )
    return format_success(
        "مسئله‌ها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_issues را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_issues",
        title=TITLE_LIST_ISSUES,
        description=LIST_ISSUES,
        annotations=READ_ONLY_CRUD,
    )
    def list_issues(
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: مسائل پروژه‌های عضو فعال بودن را می‌خواند."""
        return run_list_issues(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
