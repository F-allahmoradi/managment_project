"""ابزار MCP برای تبدیل فایل صوتی محلی به متن."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_active_actor
from business_logic.transcribe import transcribe_file
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import TRANSCRIBE_AUDIO
from mcp_server.metadata import READ_ONLY_STT, TITLE_TRANSCRIBE_AUDIO
from validators.audio import validate_transcribe_audio


@logged_tool("transcribe_audio")
def run_transcribe_audio(file_path: str, language: str = "fa-IR") -> dict:
    """مسیر کامل رونویسی فایل را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        require_active_actor()
        parsed = validate_transcribe_audio(file_path, language)
        text = transcribe_file(parsed["file_path"], parsed["language"])
        return format_success(
            "صدا به متن تبدیل شد",
            transcribed_text=text,
            language=parsed["language"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار transcribe_audio را ثبت می‌کند."""

    @mcp.tool(
        name="transcribe_audio",
        title=TITLE_TRANSCRIBE_AUDIO,
        description=TRANSCRIBE_AUDIO,
        annotations=READ_ONLY_STT,
    )
    def transcribe_audio(file_path: str, language: str = "fa-IR") -> dict:
        """ابزار MCP: فایل صوتی را با Google fa-IR به متن تبدیل می‌کند."""
        return run_transcribe_audio(file_path=file_path, language=language)
