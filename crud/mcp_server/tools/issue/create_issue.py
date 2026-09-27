"""ابزار MCP برای ثبت یک مسئله در issues و وصل تحلیل در issue_sources.

استخراج در nlp می‌ماند. علت با link_issue_cause است.
وظیفه با create_task و link_issue_task است.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_ISSUE
from mcp_server.metadata import TITLE_CREATE_ISSUE, WRITE_CRUD
from services.issue import insert_issue
from validators.issue import validate_create_issue


@run_tool("create_issue")
def run_create_issue(**fields) -> dict:
    """مسیر کامل ثبت مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_create_issue(fields)
    require_active_project_member(actor["id"], parsed["project_id"])
    stored = insert_issue(parsed, created_by=actor["id"])
    return format_success("مسئله ثبت شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار create_issue را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_issue",
        title=TITLE_CREATE_ISSUE,
        description=CREATE_ISSUE,
        annotations=WRITE_CRUD,
    )
    def create_issue(
        project_id: int,
        title: str,
        analysis_id: int,
        status: Optional[str] = None,
        status_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: ردیف issues و منبع تحلیل را می‌نویسد؛ علت جدا است."""
        payload = {
            "project_id": project_id,
            "title": title,
            "analysis_id": analysis_id,
        }
        if status is not None:
            payload["status"] = status
        if status_id is not None:
            payload["status_id"] = status_id
        return run_create_issue(**payload)
