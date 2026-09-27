"""ابزار MCP برای تنظیم فوریت مسئله از کاتالوگ task_priorities.

همان مقدار روی text_analysis_urgencies تحلیل مبدأ هم نوشته می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import SET_ISSUE_URGENCY
from mcp_server.metadata import TITLE_SET_ISSUE_URGENCY, WRITE_CRUD
from services.issue import fetch_issue_project_id, set_issue_urgency
from validators.issue import validate_set_issue_urgency


@run_tool("set_issue_urgency")
def run_set_issue_urgency(**fields) -> dict:
    """مسیر کامل تنظیم فوریت مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_set_issue_urgency(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = set_issue_urgency(parsed, created_by=actor["id"])
    return format_success("فوریت مسئله تنظیم شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار set_issue_urgency را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="set_issue_urgency",
        title=TITLE_SET_ISSUE_URGENCY,
        description=SET_ISSUE_URGENCY,
        annotations=WRITE_CRUD,
    )
    def set_issue_urgency_tool(
        issue_id: int,
        priority: Optional[str] = None,
        priority_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_urgencies می‌نویسد؛ حدس LLM نیست."""
        payload = {"issue_id": issue_id}
        if priority is not None:
            payload["priority"] = priority
        if priority_id is not None:
            payload["priority_id"] = priority_id
        return run_set_issue_urgency(**payload)
