"""ابزار MCP برای خواندن یک پروژه با شناسه از projects.

فقط پروژه‌ای که کاربر جاری عضو فعال آن است خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_PROJECT
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_PROJECT
from services.project import fetch_project
from validators.project import validate_get_project


@run_tool("get_project")
def run_get_project(id: int) -> dict:
    """مسیر کامل خواندن پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Project", "Read")
    project_id = validate_get_project(id)
    require_active_project_member(actor["id"], project_id)
    project = fetch_project(project_id)
    return format_success("پروژه خوانده شد", **project)


def register(mcp: MCPServer) -> None:
    """ابزار get_project را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_project,
        name="get_project",
        title=TITLE_GET_PROJECT,
        description=GET_PROJECT,
        annotations=READ_ONLY_CRUD,
    )
