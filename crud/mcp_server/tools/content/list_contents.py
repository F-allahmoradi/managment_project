"""ابزار MCP برای فهرست محتواهای خود کاربر جاری."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_CONTENTS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_CONTENTS
from services.content import fetch_contents_for_actor
from validators.content import validate_list_contents


@run_tool("list_contents")
def run_list_contents(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست محتواهای سازنده را اجرا می‌کند."""
    actor = require_permission("Content", "Read")
    parsed = validate_list_contents(limit=limit, offset=offset)
    records = fetch_contents_for_actor(actor["id"], parsed["limit"], parsed["offset"])
    return format_success(
        "محتواها فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_contents را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_contents,
        name="list_contents",
        title=TITLE_LIST_CONTENTS,
        description=LIST_CONTENTS,
        annotations=READ_ONLY_CRUD,
    )
