"""ابزار MCP برای ثبت یک پیگیری روی یک وظیفه.

وضعیت خود کار عوض نمی‌شود. نوع و نتیجه lookup seed هستند.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_TASK_FOLLOW_UP
from mcp_server.metadata import TITLE_CREATE_TASK_FOLLOW_UP, WRITE_CRUD
from services.task import fetch_task_project_id
from services.task_follow_up import insert_task_follow_up
from validators.task_follow_up import validate_create_task_follow_up


@run_tool("create_task_follow_up")
def run_create_task_follow_up(**fields) -> dict:
    """مسیر کامل ثبت پیگیری را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("TaskFollowUp", "Create")
    parsed = validate_create_task_follow_up(fields)
    project_id = fetch_task_project_id(parsed["task_id"])
    require_active_project_member(actor["id"], project_id)
    new_id = insert_task_follow_up(parsed, followed_by=actor["id"])
    return format_success("پیگیری ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_task_follow_up را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_task_follow_up",
        title=TITLE_CREATE_TASK_FOLLOW_UP,
        description=CREATE_TASK_FOLLOW_UP,
        annotations=WRITE_CRUD,
    )
    def create_task_follow_up(
        task_id: int,
        note: str,
        follow_up_type: Optional[str] = None,
        status: Optional[str] = None,
        follow_up_type_id: Optional[int] = None,
        status_id: Optional[int] = None,
        follow_up_date: Optional[str] = None,
        next_follow_up_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف task_follow_ups روی همان وظیفه درج می‌کند."""
        return run_create_task_follow_up(
            task_id=task_id,
            note=note,
            follow_up_type=follow_up_type,
            status=status,
            follow_up_type_id=follow_up_type_id,
            status_id=status_id,
            follow_up_date=follow_up_date,
            next_follow_up_date=next_follow_up_date,
        )
