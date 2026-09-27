"""ابزار MCP برای تیک زدن یک زیرکار (is_completed + completed_at).

فقط مسئول همان Task. یادآوری ساخته نمی‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import COMPLETE_TASK_ITEM
from mcp_server.metadata import TITLE_COMPLETE_TASK_ITEM, WRITE_CRUD
from services.task_item import complete_task_item, fetch_task_item_project_id
from validators.task_item import validate_complete_task_item


@run_tool("complete_task_item")
def run_complete_task_item(id: int, is_completed: bool = True) -> dict:
    """مسیر کامل تیک زدن زیرکار را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Update")
    parsed = validate_complete_task_item(
        {"id": id, "is_completed": is_completed}
    )
    project_id = fetch_task_item_project_id(parsed["id"])
    require_active_project_member(actor["id"], project_id)
    item_id = complete_task_item(
        parsed["id"],
        actor_id=actor["id"],
        is_completed=parsed["is_completed"],
    )
    message = (
        "زیرکار تیک زده شد"
        if parsed["is_completed"]
        else "تیک زیرکار برداشته شد"
    )
    return format_success(message, id=item_id)


def register(mcp: MCPServer) -> None:
    """ابزار complete_task_item را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="complete_task_item",
        title=TITLE_COMPLETE_TASK_ITEM,
        description=COMPLETE_TASK_ITEM,
        annotations=WRITE_CRUD,
    )
    def complete_task_item_tool(
        id: int,
        is_completed: Optional[bool] = True,
    ) -> dict:
        """ابزار MCP: زیرکار را تیک می‌زند یا تیک را برمی‌دارد."""
        completed = True if is_completed is None else is_completed
        return run_complete_task_item(id=id, is_completed=completed)
