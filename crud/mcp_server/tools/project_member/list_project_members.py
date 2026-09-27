"""ابزار MCP برای فهرست اعضای یک پروژه.

فقط اگر کاربر جاری عضو فعال همان پروژه باشد فهرست برمی‌گردد.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_PROJECT_MEMBERS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_PROJECT_MEMBERS
from services.project_member import fetch_project_members
from validators.project_member import validate_list_project_members


@run_tool("list_project_members")
def run_list_project_members(
    project_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست اعضای پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("ProjectMember", "Read")
    parsed = validate_list_project_members(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    require_active_project_member(actor["id"], parsed["project_id"])
    records = fetch_project_members(
        parsed["project_id"],
        parsed["limit"],
        parsed["offset"],
    )
    return format_success(
        "اعضای پروژه فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_project_members را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_project_members",
        title=TITLE_LIST_PROJECT_MEMBERS,
        description=LIST_PROJECT_MEMBERS,
        annotations=READ_ONLY_CRUD,
    )
    def list_project_members(
        project_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: اعضای project_members یک پروژه را می‌خواند."""
        return run_list_project_members(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
