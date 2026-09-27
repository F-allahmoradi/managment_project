"""ابزار MCP برای خواندن یک مخاطب خارجی با شناسه."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_EXTERNAL_CONTACT
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_EXTERNAL_CONTACT
from services.external_contact import fetch_external_contact
from validators.external_contact import validate_get_external_contact


@run_tool("get_external_contact")
def run_get_external_contact(id: int) -> dict:
    """مسیر کامل خواندن مخاطب خارجی را بدون دکوراتور MCP اجرا می‌کند."""
    require_permission("Message", "Read")
    contact_id = validate_get_external_contact(id)
    contact = fetch_external_contact(contact_id)
    return format_success("مخاطب خارجی خوانده شد", **contact)


def register(mcp: MCPServer) -> None:
    """ابزار get_external_contact را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_external_contact,
        name="get_external_contact",
        title=TITLE_GET_EXTERNAL_CONTACT,
        description=GET_EXTERNAL_CONTACT,
        annotations=READ_ONLY_CRUD,
    )
