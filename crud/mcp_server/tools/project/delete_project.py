"""ابزار MCP برای حذف یک پروژه خالی از projects.

وظیفه، جلسه، گزارش و وابسته‌های RESTRICT حذف را رد می‌کنند.
اعضای پروژه با CASCADE پاک می‌شوند.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_PROJECT
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_PROJECT
from services.project import delete_project
from validators.project import validate_delete_project


@run_tool("delete_project")
def run_delete_project(id: int) -> dict:
    """مسیر کامل حذف پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Project", "Delete")
    project_id = validate_delete_project(id)
    require_active_project_member(actor["id"], project_id)
    deleted_id = delete_project(project_id, actor_id=actor["id"])
    return format_success("پروژه حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_project را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_project,
        name="delete_project",
        title=TITLE_DELETE_PROJECT,
        description=DELETE_PROJECT,
        annotations=DESTRUCTIVE_CRUD,
    )
