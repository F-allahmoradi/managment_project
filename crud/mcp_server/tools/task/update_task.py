"""ابزار MCP برای به‌روزرسانی یک وظیفه در tasks.

عوض کردن وضعیت یا اولویت ردیف پیگیری نمی‌سازد.
فقط اگر عضو فعال پروژهٔ همان وظیفه باشید اجرا می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_TASK
from mcp_server.metadata import TITLE_UPDATE_TASK, WRITE_CRUD
from services.task import fetch_task_project_id, update_task
from validators.task import validate_update_task


@run_tool("update_task")
def run_update_task(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی وظیفه را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Update")
    parsed = validate_update_task({"id": id, **fields})
    project_id = fetch_task_project_id(parsed["id"])
    require_active_project_member(actor["id"], project_id)
    task_id = update_task(parsed, actor_id=actor["id"])
    return format_success("وظیفه به‌روزرسانی شد", id=task_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_task را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_task",
        title=TITLE_UPDATE_TASK,
        description=UPDATE_TASK,
        annotations=WRITE_CRUD,
    )
    def update_task_tool(
        id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        importance: Optional[str] = None,
        status_id: Optional[int] = None,
        priority_id: Optional[int] = None,
        importance_id: Optional[int] = None,
        importance_percent: Optional[int] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک وظیفه موجود را اگر عضو پروژه باشید به‌روز می‌کند."""
        return run_update_task(
            id=id,
            title=title,
            description=description,
            assigned_to_user_id=assigned_to_user_id,
            status=status,
            priority=priority,
            importance=importance,
            status_id=status_id,
            priority_id=priority_id,
            importance_id=importance_id,
            importance_percent=importance_percent,
            start_date=start_date,
            due_date=due_date,
            completed_at=completed_at,
        )
