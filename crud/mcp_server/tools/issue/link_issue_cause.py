"""ابزار MCP برای وصل دو مسئله در issue_causes.

فقط شناسهٔ مسئله، شناسهٔ علت، و سطح علت/ریشه. وظیفه اینجا نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import InvalidInputError, format_success
from mcp_server.docstrings import LINK_ISSUE_CAUSE
from mcp_server.metadata import TITLE_LINK_ISSUE_CAUSE, WRITE_CRUD
from services.issue import fetch_issue_project_id, insert_issue_cause
from validators.issue import validate_link_issue_cause


@run_tool("link_issue_cause")
def run_link_issue_cause(**fields) -> dict:
    """مسیر کامل وصل علت را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_link_issue_cause(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    cause_project_id = fetch_issue_project_id(parsed["cause_issue_id"])
    require_active_project_member(actor["id"], project_id)
    if project_id != cause_project_id:
        raise InvalidInputError("علت باید در همان پروژهٔ مسئله باشد")
    stored = insert_issue_cause(parsed, created_by=actor["id"])
    return format_success("علت به مسئله وصل شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار link_issue_cause را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="link_issue_cause",
        title=TITLE_LINK_ISSUE_CAUSE,
        description=LINK_ISSUE_CAUSE,
        annotations=WRITE_CRUD,
    )
    def link_issue_cause(
        issue_id: int,
        cause_issue_id: int,
        cause_level: Optional[str] = None,
        cause_level_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_causes می‌نویسد؛ وظیفه نمی‌نویسد."""
        payload = {
            "issue_id": issue_id,
            "cause_issue_id": cause_issue_id,
        }
        if cause_level is not None:
            payload["cause_level"] = cause_level
        if cause_level_id is not None:
            payload["cause_level_id"] = cause_level_id
        return run_link_issue_cause(**payload)
