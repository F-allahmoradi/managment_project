"""ابزار MCP برای افزودن یک گیرنده به پیام موجود.

قانون XOR: دقیقاً یکی از user_id یا external_contact_id.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_chat_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_MESSAGE_RECIPIENT
from mcp_server.metadata import TITLE_CREATE_MESSAGE_RECIPIENT, WRITE_CRUD
from services.message import fetch_message_chat_id
from services.message_recipient import insert_message_recipient
from validators.message_recipient import validate_create_message_recipient


@run_tool("create_message_recipient")
def run_create_message_recipient(
    message_id: int,
    user_id: Optional[int] = None,
    external_contact_id: Optional[int] = None,
) -> dict:
    """مسیر کامل افزودن گیرنده را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Create")
    parsed = validate_create_message_recipient(
        {
            "message_id": message_id,
            "user_id": user_id,
            "external_contact_id": external_contact_id,
        }
    )
    chat_id = fetch_message_chat_id(parsed["message_id"])
    require_chat_member(actor["id"], chat_id)
    new_id = insert_message_recipient(parsed, actor_id=actor["id"])
    return format_success("گیرنده پیام ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_message_recipient را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_message_recipient",
        title=TITLE_CREATE_MESSAGE_RECIPIENT,
        description=CREATE_MESSAGE_RECIPIENT,
        annotations=WRITE_CRUD,
    )
    def create_message_recipient(
        message_id: int,
        user_id: Optional[int] = None,
        external_contact_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف message_recipients با قانون XOR درج می‌کند."""
        return run_create_message_recipient(
            message_id=message_id,
            user_id=user_id,
            external_contact_id=external_contact_id,
        )
