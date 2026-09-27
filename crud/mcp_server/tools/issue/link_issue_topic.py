"""ابزار MCP برای وصل موضوع ذخیره‌شدهٔ NER به مسئله در issue_topics.

استخراج جدید نیست. موضوع باید روی تحلیل مبدأ مسئله باشد.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import LINK_ISSUE_TOPIC
from mcp_server.metadata import TITLE_LINK_ISSUE_TOPIC, WRITE_CRUD
from services.issue import fetch_issue_project_id, insert_issue_topic
from validators.issue import validate_link_issue_topic


@run_tool("link_issue_topic")
def run_link_issue_topic(**fields) -> dict:
    """مسیر کامل وصل موضوع به مسئله را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Issue", "Create")
    parsed = validate_link_issue_topic(fields)
    project_id = fetch_issue_project_id(parsed["issue_id"])
    require_active_project_member(actor["id"], project_id)
    stored = insert_issue_topic(parsed, created_by=actor["id"])
    return format_success("موضوع به مسئله وصل شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار link_issue_topic را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="link_issue_topic",
        title=TITLE_LINK_ISSUE_TOPIC,
        description=LINK_ISSUE_TOPIC,
        annotations=WRITE_CRUD,
    )
    def link_issue_topic(
        issue_id: int,
        topic: Optional[str] = None,
        topic_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف issue_topics می‌نویسد؛ استخراج نمی‌کند."""
        payload = {"issue_id": issue_id}
        if topic is not None:
            payload["topic"] = topic
        if topic_id is not None:
            payload["topic_id"] = topic_id
        return run_link_issue_topic(**payload)
