"""ابزار MCP برای علامت‌زدن اعلان خود کاربر به‌عنوان خوانده‌شده."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_actor
from errors.crud import format_success
from mcp_server.docstrings import MARK_NOTIFICATION_READ
from mcp_server.metadata import TITLE_MARK_NOTIFICATION_READ, WRITE_CRUD
from services.notification import mark_notification_read
from validators.notification import validate_mark_notification_read


@run_tool("mark_notification_read")
def run_mark_notification_read(id: int) -> dict:
    """مسیر کامل خوانده‌کردن اعلان خود کاربر را اجرا می‌کند."""
    actor = require_active_actor()
    notification_id = validate_mark_notification_read(id)
    row_id = mark_notification_read(notification_id, actor["id"])
    return format_success("اعلان خوانده شد", id=row_id)


def register(mcp: MCPServer) -> None:
    """ابزار mark_notification_read را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_mark_notification_read,
        name="mark_notification_read",
        title=TITLE_MARK_NOTIFICATION_READ,
        description=MARK_NOTIFICATION_READ,
        annotations=WRITE_CRUD,
    )
