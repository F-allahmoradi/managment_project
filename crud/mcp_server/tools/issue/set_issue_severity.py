"""ابزار MCP برای تنظیم شدت مسئله از کاتالوگ severity_levels.

شدت از اهمیت و فوریت جدا است. تحلیل مبدأ اینجا به‌روز نمی‌شود.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import SET_ISSUE_SEVERITY
from mcp_server.metadata import TITLE_SET_ISSUE_SEVERITY, WRITE_CRUD
from services.issue import fetch_issue_project_id, set_issue_severity
from validators.issue import validate_set_issue_severity


@run_tool("set_issue_severity")
def run_set_issue_severity(**fields) -> dict:
    """مسیر کامل تنظیم شدت مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_set_issue_severity(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = set_issue_severity(parsed, created_by=actor["id"])
    return format_success("شدت مسئله تنظیم شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار set_issue_severity را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="set_issue_severity",
        title=TITLE_SET_ISSUE_SEVERITY,
        description=SET_ISSUE_SEVERITY,
        annotations=WRITE_CRUD,
    )
    def set_issue_severity_tool(
        issue_id: int,
        severity: Optional[str] = None,
        severity_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_severities می‌نویسد؛ حدس LLM نیست."""
        payload = {"issue_id": issue_id}
        if severity is not None:
            payload["severity"] = severity
        if severity_id is not None:
            payload["severity_id"] = severity_id
        return run_set_issue_severity(**payload)
