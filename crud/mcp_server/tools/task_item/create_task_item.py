"""ابزار MCP برای ثبت زیرکار سطح اول یا تو در تو در task_items.

فقط مسئول همان Task می‌تواند بسازد. یادآوری از تاریخ ساخته نمی‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_TASK_ITEM
from mcp_server.metadata import TITLE_CREATE_TASK_ITEM, WRITE_CRUD
from services.task import fetch_task_project_id
from services.task_item import insert_task_item
from validators.task_item import validate_create_task_item


@run_tool("create_task_item")
def run_create_task_item(**fields) -> dict:
    """مسیر کامل ثبت زیرکار را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Update")
    parsed = validate_create_task_item(fields)
    project_id = fetch_task_project_id(parsed["task_id"])
    require_active_project_member(actor["id"], project_id)
    new_id = insert_task_item(parsed, actor_id=actor["id"])
    return format_success("زیرکار ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_task_item را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_task_item",
        title=TITLE_CREATE_TASK_ITEM,
        description=CREATE_TASK_ITEM,
        annotations=WRITE_CRUD,
    )
    def create_task_item(
        task_id: int,
        title: str,
        parent_item_id: Optional[int] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف task_items زیر همان وظیفه درج می‌کند."""
        return run_create_task_item(
            task_id=task_id,
            title=title,
            parent_item_id=parent_item_id,
            description=description,
            sort_order=sort_order,
            start_date=start_date,
            end_date=end_date,
        )
