"""ابزار MCP برای ارسال یادآوری روی کانال INTERNAL."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.dispatcher import dispatch_reminder
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import SEND_REMINDER
from mcp_server.metadata import TITLE_SEND_REMINDER, WRITE_REMINDER
from schemas.input import validate_dispatch_reminder


@logged_tool("send_reminder")
def run_send_reminder(**fields) -> dict:
    """مسیر کامل ارسال اول را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Reminder", "Dispatch")
        parsed = validate_dispatch_reminder(fields)
        records = dispatch_reminder(parsed, actor_id=actor["id"], retry=False)
        replayed = sum(1 for row in records if row.get("replayed"))
        return format_success(
            "یادآوری ارسال شد" if replayed < len(records) else "ارسال تکراری بود",
            records=records,
            sent_count=len(records) - replayed,
            replayed_count=replayed,
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار send_reminder را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="send_reminder",
        title=TITLE_SEND_REMINDER,
        description=SEND_REMINDER,
        annotations=WRITE_REMINDER,
    )
    def send_reminder(
        reminder_id: int,
        target_user_id: Optional[int] = None,
        target_external_contact_id: Optional[int] = None,
        channel: str = "INTERNAL",
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یادآوری را روی INTERNAL می‌فرستد و execution_logs می‌نویسد."""
        return run_send_reminder(
            reminder_id=reminder_id,
            target_user_id=target_user_id,
            target_external_contact_id=target_external_contact_id,
            channel=channel,
            idempotency_key=idempotency_key,
        )
