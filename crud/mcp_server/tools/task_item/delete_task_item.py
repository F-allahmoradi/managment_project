"""ابزار MCP برای حذف یک زیرکار؛ فرزندها با CASCADE پاک می‌شوند.

فقط مسئول همان Task. مجوز Task/Update است نه حذف خود وظیفه.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_TASK_ITEM
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_TASK_ITEM
from services.task_item import delete_task_item, fetch_task_item_project_id
from validators.task_item import validate_delete_task_item


@run_tool("delete_task_item")
def run_delete_task_item(id: int) -> dict:
    """مسیر کامل حذف زیرکار را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Task", "Update")
    item_id = validate_delete_task_item(id)
    project_id = fetch_task_item_project_id(item_id)
    require_active_project_member(actor["id"], project_id)
    deleted_id = delete_task_item(item_id, actor_id=actor["id"])
    return format_success("زیرکار حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_task_item را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_task_item,
        name="delete_task_item",
        title=TITLE_DELETE_TASK_ITEM,
        description=DELETE_TASK_ITEM,
        annotations=DESTRUCTIVE_CRUD,
    )
