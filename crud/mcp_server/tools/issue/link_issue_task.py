"""ابزار MCP برای وصل مسئله به وظیفهٔ موجود در issue_tasks.

ساخت وظیفه مال create_task است. اینجا فقط لینک نازک است.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import InvalidInputError, format_success
from mcp_server.docstrings import LINK_ISSUE_TASK
from mcp_server.metadata import TITLE_LINK_ISSUE_TASK, WRITE_CRUD
from services.issue import fetch_issue_project_id, insert_issue_task
from services.task import fetch_task_project_id
from validators.issue import validate_link_issue_task


@run_tool("link_issue_task")
def run_link_issue_task(**fields) -> dict:
    """مسیر کامل وصل وظیفه به مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_link_issue_task(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    task_project_id = fetch_task_project_id(parsed["task_id"])
    require_active_project_member(actor["id"], project_id)
    if project_id != task_project_id:
        raise InvalidInputError("وظیفه باید در همان پروژهٔ مسئله باشد")
    stored = insert_issue_task(parsed, created_by=actor["id"])
    return format_success("وظیفه به مسئله وصل شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار link_issue_task را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="link_issue_task",
        title=TITLE_LINK_ISSUE_TASK,
        description=LINK_ISSUE_TASK,
        annotations=WRITE_CRUD,
    )
    def link_issue_task(
        issue_id: int,
        task_id: int,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_tasks می‌نویسد؛ وظیفه نمی‌سازد."""
        return run_link_issue_task(issue_id=issue_id, task_id=task_id)
