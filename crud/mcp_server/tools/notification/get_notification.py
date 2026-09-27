"""ابزار MCP برای خواندن یک اعلان خود کاربر جاری."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_active_actor
from errors.crud import format_success
from mcp_server.docstrings import GET_NOTIFICATION
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_NOTIFICATION
from services.notification import fetch_own_notification
from validators.notification import validate_get_notification


@run_tool("get_notification")
def run_get_notification(id: int) -> dict:
    """مسیر کامل خواندن اعلان خود کاربر را اجرا می‌کند."""
    actor = require_active_actor()
    notification_id = validate_get_notification(id)
    row = fetch_own_notification(notification_id, actor["id"])
    payload = format_success("اعلان خوانده شد")
    payload.update(row)
    return payload


def register(mcp: MCPServer) -> None:
    """ابزار get_notification را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_notification,
        name="get_notification",
        title=TITLE_GET_NOTIFICATION,
        description=GET_NOTIFICATION,
        annotations=READ_ONLY_CRUD,
    )
