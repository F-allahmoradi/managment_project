"""ابزار MCP برای به‌روزرسانی یک پروژه در projects.

فقط اگر کاربر جاری عضو فعال همان پروژه باشد اجرا می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_PROJECT
from mcp_server.metadata import TITLE_UPDATE_PROJECT, WRITE_CRUD
from services.project import update_project
from validators.project import validate_update_project


@run_tool("update_project")
def run_update_project(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Project", "Update")
    parsed = validate_update_project({"id": id, **fields})
    require_active_project_member(actor["id"], parsed["id"])
    project_id = update_project(parsed, actor_id=actor["id"])
    return format_success("پروژه به‌روزرسانی شد", id=project_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_project را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_project",
        title=TITLE_UPDATE_PROJECT,
        description=UPDATE_PROJECT,
        annotations=WRITE_CRUD,
    )
    def update_project_tool(
        id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_type: Optional[str] = None,
        project_status: Optional[str] = None,
        project_type_id: Optional[int] = None,
        project_status_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک پروژه موجود را اگر عضو فعال باشید به‌روز می‌کند."""
        return run_update_project(
            id=id,
            name=name,
            description=description,
            project_type=project_type,
            project_status=project_status,
            project_type_id=project_type_id,
            project_status_id=project_status_id,
            start_date=start_date,
            end_date=end_date,
        )
