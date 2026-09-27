"""ابزار MCP برای فهرست/درخت زیرکارهای یک وظیفه.

ترتیب هر سطح sort_order است. عضو فعال پروژه می‌تواند بخواند.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_TASK_ITEMS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_TASK_ITEMS
from services.task import fetch_task_project_id
from services.task_item import fetch_task_items
from validators.task_item import validate_list_task_items


@run_tool("list_task_items")
def run_list_task_items(task_id: int) -> dict:
    """مسیر کامل فهرست زیرکارهای یک وظیفه را اجرا می‌کند."""
    actor = require_permission("Task", "Read")
    parsed_task_id = validate_list_task_items(task_id)
    project_id = fetch_task_project_id(parsed_task_id)
    require_active_project_member(actor["id"], project_id)
    payload = fetch_task_items(parsed_task_id)
    return format_success(
        "زیرکارها فهرست شدند",
        records=payload["records"],
        tree=payload["tree"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_task_items را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_task_items",
        title=TITLE_LIST_TASK_ITEMS,
        description=LIST_TASK_ITEMS,
        annotations=READ_ONLY_CRUD,
    )
    def list_task_items(task_id: int) -> dict:
        """ابزار MCP: زیرکارهای یک وظیفه را تخت و درختی می‌خواند."""
        return run_list_task_items(task_id=task_id)
