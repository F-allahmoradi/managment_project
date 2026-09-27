"""ابزار MCP برای خواندن یک ردیف ممیزی با شناسه."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_AUDIT_LOG
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_AUDIT_LOG
from services.audit_log import fetch_audit_log
from validators.audit_log import validate_get_audit_log


@run_tool("get_audit_log")
def run_get_audit_log(id: int) -> dict:
    """مسیر کامل خواندن یک ردیف ممیزی را اجرا می‌کند."""
    require_permission("AuditLog", "Read")
    row_id = validate_get_audit_log(id)
    row = fetch_audit_log(row_id)
    return format_success("ممیزی خوانده شد", **row)


def register(mcp: MCPServer) -> None:
    """ابزار get_audit_log را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_audit_log,
        name="get_audit_log",
        title=TITLE_GET_AUDIT_LOG,
        description=GET_AUDIT_LOG,
        annotations=READ_ONLY_CRUD,
    )
