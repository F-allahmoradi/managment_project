"""ابزار MCP برای حذف نرم متن رونویسی از contents."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.transcribe import delete_transcript_content
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import DELETE_TRANSCRIPT
from mcp_server.metadata import DESTRUCTIVE_STT, TITLE_DELETE_TRANSCRIPT
from validators.audio import validate_delete_transcript


@logged_tool("delete_transcript")
def run_delete_transcript(id: int) -> dict:
    """مسیر کامل حذف متن ذخیره‌شده را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Content", "Delete")
        parsed_id = validate_delete_transcript(id)
        deleted_id = delete_transcript_content(parsed_id, actor_id=actor["id"])
        return format_success("متن استخراج‌شده حذف شد", id=deleted_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار delete_transcript را ثبت می‌کند."""

    @mcp.tool(
        name="delete_transcript",
        title=TITLE_DELETE_TRANSCRIPT,
        description=DELETE_TRANSCRIPT,
        annotations=DESTRUCTIVE_STT,
    )
    def delete_transcript(id: int) -> dict:
        """ابزار MCP: ردیف contents مربوط به رونویسی را نرم‌حذف می‌کند."""
        return run_delete_transcript(id=id)
