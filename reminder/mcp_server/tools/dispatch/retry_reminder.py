"""ابزار MCP برای تلاش مجدد ارسال یادآوری روی کانال INTERNAL."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.dispatcher import dispatch_reminder
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import RETRY_REMINDER
from mcp_server.metadata import TITLE_RETRY_REMINDER, WRITE_REMINDER
from schemas.input import validate_dispatch_reminder


@logged_tool("retry_reminder")
def run_retry_reminder(**fields) -> dict:
    """مسیر کامل تلاش مجدد را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Dispatch")
        parsed = validate_dispatch_reminder(fields)
        records = dispatch_reminder(parsed, actor_id=actor["id"], retry=True)
        replayed = sum(1 for row in records if row.get("replayed"))
        return format_success(
            "تلاش مجدد ارسال شد" if replayed < len(records) else "تلاش مجدد تکراری بود",
            records=records,
            sent_count=len(records) - replayed,
            replayed_count=replayed,
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار retry_reminder را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="retry_reminder",
        title=TITLE_RETRY_REMINDER,
        description=RETRY_REMINDER,
        annotations=WRITE_REMINDER,
    )
    def retry_reminder(
        reminder_id: int,
        target_user_id: Optional[int] = None,
        target_external_contact_id: Optional[int] = None,
        channel: str = "INTERNAL",
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: تلاش بعدی ارسال را با کلید idempotency جدا می‌نویسد."""
        return run_retry_reminder(
            reminder_id=reminder_id,
            target_user_id=target_user_id,
            target_external_contact_id=target_external_contact_id,
            channel=channel,
            idempotency_key=idempotency_key,
        )
