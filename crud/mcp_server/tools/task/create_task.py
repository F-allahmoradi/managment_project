"""ابزار MCP برای ثبت یک وظیفه جدید در tasks.

مسئول باید عضو فعال همان پروژه باشد. پیگیری اینجا ساخته نمی‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_TASK
from mcp_server.metadata import TITLE_CREATE_TASK, WRITE_CRUD
from services.task import insert_task
from validators.task import validate_create_task


@run_tool("create_task")
def run_create_task(**fields) -> dict:
    """مسیر کامل ثبت وظیفه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Create")
    parsed = validate_create_task(fields)
    require_active_project_member(actor["id"], parsed["project_id"])
    new_id = insert_task(parsed, created_by=actor["id"])
    return format_success("وظیفه ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_task را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_task",
        title=TITLE_CREATE_TASK,
        description=CREATE_TASK,
        annotations=WRITE_CRUD,
    )
    def create_task(
        project_id: int,
        title: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        importance: Optional[str] = None,
        status_id: Optional[int] = None,
        priority_id: Optional[int] = None,
        importance_id: Optional[int] = None,
        assigned_to_user_id: Optional[int] = None,
        description: Optional[str] = None,
        importance_percent: Optional[int] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف tasks درج می‌کند؛ پیگیری نمی‌سازد."""
        return run_create_task(
            project_id=project_id,
            title=title,
            status=status,
            priority=priority,
            importance=importance,
            status_id=status_id,
            priority_id=priority_id,
            importance_id=importance_id,
            assigned_to_user_id=assigned_to_user_id,
            description=description,
            importance_percent=importance_percent,
            start_date=start_date,
            due_date=due_date,
        )
