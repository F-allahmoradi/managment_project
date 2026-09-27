"""ابزار MCP برای نوشتن متن رونویسی و در صورت وجود، فایل صوت."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.transcribe import save_transcript_text, save_voice_from_path
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import SAVE_TRANSCRIPT
from mcp_server.metadata import TITLE_SAVE_TRANSCRIPT, WRITE_STT
from validators.audio import validate_save_transcript


@logged_tool("save_transcript")
def run_save_transcript(
    text: str,
    file_path: Optional[str] = None,
    mime_type: Optional[str] = None,
    original_filename: Optional[str] = None,
) -> dict:
    """مسیر کامل ذخیره متن و صوت را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Content", "Create")
        parsed = validate_save_transcript(
            text,
            file_path=file_path,
            mime_type=mime_type,
            original_filename=original_filename,
        )
        if parsed.get("file_path"):
            new_id = save_voice_from_path(
                parsed["text"],
                parsed["file_path"],
                created_by=actor["id"],
                mime_type=parsed.get("mime_type"),
                original_filename=parsed.get("original_filename"),
            )
            return format_success(
                "متن و فایل صوت ذخیره شد",
                id=new_id,
                content_kind="VOICE",
            )
        new_id = save_transcript_text(parsed["text"], created_by=actor["id"])
        return format_success("متن استخراج‌شده ذخیره شد", id=new_id, content_kind="TEXT")
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار save_transcript را ثبت می‌کند."""

    @mcp.tool(
        name="save_transcript",
        title=TITLE_SAVE_TRANSCRIPT,
        description=SAVE_TRANSCRIPT,
        annotations=WRITE_STT,
    )
    def save_transcript(
        text: str,
        file_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: متن و در صورت مسیر فایل، خود صوت را در contents می‌نویسد."""
        return run_save_transcript(
            text=text,
            file_path=file_path,
            mime_type=mime_type,
            original_filename=original_filename,
        )
