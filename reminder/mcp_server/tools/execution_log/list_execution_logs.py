"""ابزار MCP برای خواندن لاگ ارسال یک یادآوری."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.dispatcher import fetch_execution_logs
from business_logic.follow_up import require_reminder_access
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_EXECUTION_LOGS
from mcp_server.metadata import READ_ONLY_REMINDER, TITLE_LIST_EXECUTION_LOGS
from schemas.input import validate_list_execution_logs


@logged_tool("list_execution_logs")
def run_list_execution_logs(
    reminder_id: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست لاگ ارسال را اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Read")
        parsed = validate_list_execution_logs(
            reminder_id=reminder_id,
            limit=limit,
            offset=offset,
        )
        require_reminder_access(actor["id"], parsed["reminder_id"])
        records = fetch_execution_logs(
            parsed["reminder_id"],
            parsed["limit"],
            parsed["offset"],
        )
        return format_success(
            "لاگ ارسال فهرست شد",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_execution_logs را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_execution_logs",
        title=TITLE_LIST_EXECUTION_LOGS,
        description=LIST_EXECUTION_LOGS,
        annotations=READ_ONLY_REMINDER,
    )
    def list_execution_logs(
        reminder_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: execution_logs یک یادآوری را می‌خواند."""
        return run_list_execution_logs(
            reminder_id=reminder_id,
            limit=limit,
            offset=offset,
        )
