"""ابزار MCP برای افزودن یک اثر مسئله از کاتالوگ impact_types.

هر فراخوانی یک ردیف issue_impacts می‌نویسد. موضوع و موجودیت اینجا نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import ADD_ISSUE_IMPACT
from mcp_server.metadata import TITLE_ADD_ISSUE_IMPACT, WRITE_CRUD
from services.issue import add_issue_impact, fetch_issue_project_id
from validators.issue import validate_add_issue_impact


@run_tool("add_issue_impact")
def run_add_issue_impact(**fields) -> dict:
    """مسیر کامل افزودن اثر مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_add_issue_impact(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = add_issue_impact(parsed, created_by=actor["id"])
    return format_success("اثر به مسئله اضافه شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار add_issue_impact را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="add_issue_impact",
        title=TITLE_ADD_ISSUE_IMPACT,
        description=ADD_ISSUE_IMPACT,
        annotations=WRITE_CRUD,
    )
    def add_issue_impact_tool(
        issue_id: int,
        impact_type: Optional[str] = None,
        impact_type_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_impacts می‌نویسد؛ یادآوری نمی‌فرستد."""
        payload = {"issue_id": issue_id}
        if impact_type is not None:
            payload["impact_type"] = impact_type
        if impact_type_id is not None:
            payload["impact_type_id"] = impact_type_id
        if description is not None:
            payload["description"] = description
        return run_add_issue_impact(**payload)
