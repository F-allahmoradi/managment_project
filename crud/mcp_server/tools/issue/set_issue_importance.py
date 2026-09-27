"""ابزار MCP برای تنظیم اهمیت مسئله از کاتالوگ task_importances.

همان مقدار روی text_analysis_importances تحلیل مبدأ هم نوشته می‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import SET_ISSUE_IMPORTANCE
from mcp_server.metadata import TITLE_SET_ISSUE_IMPORTANCE, WRITE_CRUD
from services.issue import fetch_issue_project_id, set_issue_importance
from validators.issue import validate_set_issue_importance


@run_tool("set_issue_importance")
def run_set_issue_importance(**fields) -> dict:
    """مسیر کامل تنظیم اهمیت مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_set_issue_importance(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = set_issue_importance(parsed, created_by=actor["id"])
    return format_success("اهمیت مسئله تنظیم شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار set_issue_importance را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="set_issue_importance",
        title=TITLE_SET_ISSUE_IMPORTANCE,
        description=SET_ISSUE_IMPORTANCE,
        annotations=WRITE_CRUD,
    )
    def set_issue_importance_tool(
        issue_id: int,
        importance: Optional[str] = None,
        importance_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_importances می‌نویسد؛ حدس LLM نیست."""
        payload = {"issue_id": issue_id}
        if importance is not None:
            payload["importance"] = importance
        if importance_id is not None:
            payload["importance_id"] = importance_id
        return run_set_issue_importance(**payload)
