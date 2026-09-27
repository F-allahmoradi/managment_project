"""ابزار MCP برای فهرست مخاطبان خارج از سامانه."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_EXTERNAL_CONTACTS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_EXTERNAL_CONTACTS
from services.external_contact import fetch_external_contacts
from validators.external_contact import validate_list_external_contacts


@run_tool("list_external_contacts")
def run_list_external_contacts(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست مخاطبان خارجی را اجرا می‌کند."""
    require_permission("Message", "Read")
    parsed = validate_list_external_contacts(limit=limit, offset=offset)
    records = fetch_external_contacts(parsed["limit"], parsed["offset"])
    return format_success(
        "مخاطبان خارجی فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_external_contacts را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_external_contacts,
        name="list_external_contacts",
        title=TITLE_LIST_EXTERNAL_CONTACTS,
        description=LIST_EXTERNAL_CONTACTS,
        annotations=READ_ONLY_CRUD,
    )
