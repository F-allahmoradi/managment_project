"""ابزار MCP برای ارسال پیام متنی داخل گفتگو.

content_id نوشته نمی‌شود. گیرنده‌ها همان لحظه در message_recipients
ساخته می‌شوند. XOR روی هر ردیف گیرنده است، نه روی کل پیام.
گفتگوی پروژه به پروژه وصل است و تسک اختیاری است؛ گفتگوی خصوصی تسک ندارد.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_MESSAGE
from mcp_server.metadata import TITLE_CREATE_MESSAGE, WRITE_CRUD
from services.message import insert_message
from validators.message import validate_create_message


@run_tool("create_message")
def run_create_message(**fields) -> dict:
    """مسیر کامل ارسال پیام را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Create")
    parsed = validate_create_message(fields)
    require_chat_member(actor["id"], parsed["chat_id"])
    new_id = insert_message(parsed, sender_user_id=actor["id"])
    return format_success("پیام ارسال شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_message را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_message",
        title=TITLE_CREATE_MESSAGE,
        description=CREATE_MESSAGE,
        annotations=WRITE_CRUD,
    )
    def create_message(
        chat_id: int,
        text: str,
        task_id: Optional[int] = None,
        recipient_user_id: Optional[int] = None,
        recipient_external_contact_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: messages و گیرنده‌ها را درج می‌کند؛ content_id نمی‌نویسد."""
        return run_create_message(
            chat_id=chat_id,
            task_id=task_id,
            text=text,
            recipient_user_id=recipient_user_id,
            recipient_external_contact_id=recipient_external_contact_id,
        )
