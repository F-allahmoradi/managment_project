"""ابزار MCP برای فهرست ممیزی سامانه.

مجوز AuditLog/Read لازم است. ساختن دستی از چت نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_AUDIT_LOGS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_AUDIT_LOGS
from services.audit_log import fetch_audit_logs
from validators.audit_log import validate_list_audit_logs


@run_tool("list_audit_logs")
def run_list_audit_logs(
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست ممیزی را اجرا می‌کند."""
    require_permission("AuditLog", "Read")
    parsed = validate_list_audit_logs(
        entity=entity,
        entity_id=entity_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    records = fetch_audit_logs(
        parsed["limit"],
        parsed["offset"],
        entity=parsed.get("entity"),
        entity_id=parsed.get("entity_id"),
        user_id=parsed.get("user_id"),
    )
    return format_success(
        "ممیزی فهرست شد",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_audit_logs را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_audit_logs",
        title=TITLE_LIST_AUDIT_LOGS,
        description=LIST_AUDIT_LOGS,
        annotations=READ_ONLY_CRUD,
    )
    def list_audit_logs(
        entity: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: ردیف‌های audit_logs را با مجوز AuditLog/Read می‌خواند."""
        return run_list_audit_logs(
            entity=entity,
            entity_id=entity_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
