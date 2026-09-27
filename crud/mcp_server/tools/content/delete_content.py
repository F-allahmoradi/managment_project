"""ابزار MCP برای حذف نرم یک محتوا از contents.

اگر به مستند پروژه وصل باشد حذف رد می‌شود. صوت خام روی S3 نیست.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_CONTENT
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_CONTENT
from services.content import delete_content
from validators.content import validate_delete_content


@run_tool("delete_content")
def run_delete_content(id: int) -> dict:
    """مسیر کامل حذف محتوا را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Content", "Delete")
    content_id = validate_delete_content(id)
    deleted_id = delete_content(content_id, actor_id=actor["id"])
    return format_success("محتوا حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_content را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_delete_content,
        name="delete_content",
        title=TITLE_DELETE_CONTENT,
        description=DELETE_CONTENT,
        annotations=DESTRUCTIVE_CRUD,
    )
