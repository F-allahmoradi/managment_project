"""ابزار MCP برای خواندن یک مسئله با شناسه از issues.

فقط اگر کاربر جاری عضو فعال پروژهٔ همان مسئله باشد خوانده می‌شود.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_ISSUE
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_ISSUE
from services.issue import fetch_issue, fetch_issue_project_id
from validators.issue import validate_get_issue


@run_tool("get_issue")
def run_get_issue(id: int) -> dict:
    """مسیر کامل خواندن مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Read")
    issue_id = validate_get_issue(id)
    project_id = fetch_issue_project_id(issue_id)
    require_active_project_member(actor["id"], project_id)
    issue = fetch_issue(issue_id)
    return format_success("مسئله خوانده شد", **issue)


def register(mcp: MCPServer) -> None:
    """ابزار get_issue را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_issue,
        name="get_issue",
        title=TITLE_GET_ISSUE,
        description=GET_ISSUE,
        annotations=READ_ONLY_CRUD,
    )
