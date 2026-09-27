"""ابزار MCP برای به‌روزرسانی عنوان، ترتیب یا تاریخ یک زیرکار.

تیک زدن مال complete_task_item است. فقط مسئول همان Task.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_TASK_ITEM
from mcp_server.metadata import TITLE_UPDATE_TASK_ITEM, WRITE_CRUD
from services.task_item import fetch_task_item_project_id, update_task_item
from validators.task_item import validate_update_task_item


@run_tool("update_task_item")
def run_update_task_item(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی زیرکار را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Update")
    parsed = validate_update_task_item({"id": id, **fields})
    project_id = fetch_task_item_project_id(parsed["id"])
    require_active_project_member(actor["id"], project_id)
    item_id = update_task_item(parsed, actor_id=actor["id"])
    return format_success("زیرکار به‌روزرسانی شد", id=item_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_task_item را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_task_item",
        title=TITLE_UPDATE_TASK_ITEM,
        description=UPDATE_TASK_ITEM,
        annotations=WRITE_CRUD,
    )
    def update_task_item_tool(
        id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: عنوان، ترتیب یا تاریخ زیرکار را اگر مسئول باشید عوض می‌کند."""
        return run_update_task_item(
            id=id,
            title=title,
            description=description,
            sort_order=sort_order,
            start_date=start_date,
            end_date=end_date,
        )
