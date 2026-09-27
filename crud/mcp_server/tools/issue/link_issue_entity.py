"""ابزار MCP برای وصل موجودیت ذخیره‌شدهٔ NER به مسئله با نقش seed.

نقش از issue_entity_roles است. استخراج جدید و entity_relations نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LINK_ISSUE_ENTITY
from mcp_server.metadata import TITLE_LINK_ISSUE_ENTITY, WRITE_CRUD
from services.issue import fetch_issue_project_id, insert_issue_entity
from validators.issue import validate_link_issue_entity


@run_tool("link_issue_entity")
def run_link_issue_entity(**fields) -> dict:
    """مسیر کامل وصل موجودیت به مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_link_issue_entity(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = insert_issue_entity(parsed, created_by=actor["id"])
    return format_success("موجودیت به مسئله وصل شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار link_issue_entity را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="link_issue_entity",
        title=TITLE_LINK_ISSUE_ENTITY,
        description=LINK_ISSUE_ENTITY,
        annotations=WRITE_CRUD,
    )
    def link_issue_entity(
        issue_id: int,
        entity_id: int,
        role: Optional[str] = None,
        role_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_entities می‌نویسد؛ یادآوری نمی‌فرستد."""
        payload = {"issue_id": issue_id, "entity_id": entity_id}
        if role is not None:
            payload["role"] = role
        if role_id is not None:
            payload["role_id"] = role_id
        return run_link_issue_entity(**payload)
