"""ابزار MCP برای ضبط میکروفون همین ماشین و تبدیل به متن."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.transcribe import listen_and_transcribe
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import RECORD_AUDIO_TO_TEXT
from mcp_server.metadata import TITLE_RECORD_AUDIO_TO_TEXT, WRITE_STT
from validators.audio import validate_record_audio


@logged_tool("record_audio_to_text")
def run_record_audio_to_text(
    language: str = "fa-IR",
    timeout: int = 5,
    phrase_time_limit: int = 10,
    quality: str = "medium",
) -> dict:
    """مسیر کامل ضبط میکروفون را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        require_permission("Content", "Create")
        parsed = validate_record_audio(
            language=language,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            quality=quality,
        )
        text = listen_and_transcribe(
            language=parsed["language"],
            timeout=parsed["timeout"],
            phrase_time_limit=parsed["phrase_time_limit"],
            quality=parsed["quality"],
        )
        return format_success(
            "صدا ضبط و به متن تبدیل شد",
            transcribed_text=text,
            language=parsed["language"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار record_audio_to_text را ثبت می‌کند."""

    @mcp.tool(
        name="record_audio_to_text",
        title=TITLE_RECORD_AUDIO_TO_TEXT,
        description=RECORD_AUDIO_TO_TEXT,
        annotations=WRITE_STT,
    )
    def record_audio_to_text(
        language: str = "fa-IR",
        timeout: int = 5,
        phrase_time_limit: int = 10,
        quality: str = "medium",
    ) -> dict:
        """ابزار MCP: میکروفون سرور را باز می‌کند و متن فارسی برمی‌گرداند."""
        return run_record_audio_to_text(
            language=language,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            quality=quality,
        )
