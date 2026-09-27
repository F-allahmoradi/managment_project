"""ابزار MCP برای ثبت مخاطب خارج از سامانه.

ردیف users ساخته نمی‌شود. ارسال واقعی تلگرام/SMS در این گام نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_EXTERNAL_CONTACT
from mcp_server.metadata import TITLE_CREATE_EXTERNAL_CONTACT, WRITE_CRUD
from services.external_contact import insert_external_contact
from validators.external_contact import validate_create_external_contact


@run_tool("create_external_contact")
def run_create_external_contact(**fields) -> dict:
    """مسیر کامل ثبت مخاطب خارجی را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Message", "Create")
    parsed = validate_create_external_contact(fields)
    new_id = insert_external_contact(parsed, actor_id=actor["id"])
    return format_success("مخاطب خارجی ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_external_contact را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_external_contact",
        title=TITLE_CREATE_EXTERNAL_CONTACT,
        description=CREATE_EXTERNAL_CONTACT,
        annotations=WRITE_CRUD,
    )
    def create_external_contact(
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        telegram_id: Optional[str] = None,
        is_active: bool = True,
    ) -> dict:
        """ابزار MCP: یک ردیف external_contacts درج می‌کند؛ users دست نمی‌خورد."""
        return run_create_external_contact(
            name=name,
            phone=phone,
            email=email,
            telegram_id=telegram_id,
            is_active=is_active,
        )
