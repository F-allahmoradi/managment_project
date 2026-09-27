"""ابزار MCP برای فهرست پروژه‌های قابل‌مشاهدهٔ کاربر جاری.

فقط پروژه‌هایی برمی‌گردد که کاربر عضو فعال‌شان است، نه همهٔ جدول.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_PROJECTS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_PROJECTS
from services.project import fetch_projects_for_actor
from validators.project import validate_list_projects


@run_tool("list_projects")
def run_list_projects(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست پروژه‌های کاربر جاری را اجرا می‌کند."""
    actor = require_permission("Project", "Read")
    parsed_limit, parsed_offset = validate_list_projects(
        limit=limit,
        offset=offset,
    )
    records = fetch_projects_for_actor(
        actor["id"],
        parsed_limit,
        parsed_offset,
    )
    return format_success(
        "پروژه‌ها فهرست شدند",
        records=records,
        limit=parsed_limit,
        offset=parsed_offset,
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_projects را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_projects,
        name="list_projects",
        title=TITLE_LIST_PROJECTS,
        description=LIST_PROJECTS,
        annotations=READ_ONLY_CRUD,
    )
