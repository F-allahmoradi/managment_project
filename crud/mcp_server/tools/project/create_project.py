"""ابزار MCP برای ثبت یک پروژه جدید در projects.

سازنده به‌عنوان عضو با نقش «مدیر پروژه» وارد project_members می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_PROJECT
from mcp_server.metadata import TITLE_CREATE_PROJECT, WRITE_CRUD
from services.project import insert_project
from validators.project import validate_create_project


@run_tool("create_project")
def run_create_project(**fields) -> dict:
    """مسیر کامل ثبت پروژه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Project", "Create")
    parsed = validate_create_project(fields)
    new_id = insert_project(parsed, created_by=actor["id"])
    return format_success("پروژه ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_project را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_project",
        title=TITLE_CREATE_PROJECT,
        description=CREATE_PROJECT,
        annotations=WRITE_CRUD,
    )
    def create_project(
        name: str,
        project_type: Optional[str] = None,
        project_status: Optional[str] = None,
        project_type_id: Optional[int] = None,
        project_status_id: Optional[int] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک پروژه در projects درج می‌کند و سازنده را عضو می‌کند."""
        return run_create_project(
            name=name,
            project_type=project_type,
            project_status=project_status,
            project_type_id=project_type_id,
            project_status_id=project_status_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
        )
