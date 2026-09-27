"""ثبت ابزارهای ضبط و تبدیل گفتار روی سرور MCP."""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.delete_transcript import (
    register as register_delete_transcript,
)
from mcp_server.tools.record_audio_to_text import (
    register as register_record_audio_to_text,
)
from mcp_server.tools.save_transcript import register as register_save_transcript
from mcp_server.tools.transcribe_audio import register as register_transcribe_audio


def register_stt_tools(mcp: MCPServer) -> None:
    """ابزارهای رونویسی فایل، ضبط میکروفون، ذخیره و حذف متن را ثبت می‌کند."""
    setup_logging()
    register_transcribe_audio(mcp)
    register_record_audio_to_text(mcp)
    register_save_transcript(mcp)
    register_delete_transcript(mcp)
