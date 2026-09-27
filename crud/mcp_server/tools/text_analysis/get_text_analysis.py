"""ابزار MCP برای خواندن یک اجرای تحلیل متن با ذکرهای ذخیره‌شده."""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_TEXT_ANALYSIS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_TEXT_ANALYSIS
from services.text_analysis import fetch_text_analysis
from validators.text_analysis import validate_get_text_analysis


@run_tool("get_text_analysis")
def run_get_text_analysis(id: int) -> dict:
    """مسیر کامل خواندن تحلیل متن را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("TextAnalysis", "Read")
    analysis_id = validate_get_text_analysis(id)
    row = fetch_text_analysis(analysis_id, actor["id"])
    return format_success("تحلیل متن خوانده شد", **row)


def register(mcp: MCPServer) -> None:
    """ابزار get_text_analysis را روی نمونه سرور ثبت می‌کند."""
    register_id_tool(
        mcp,
        run_get_text_analysis,
        name="get_text_analysis",
        title=TITLE_GET_TEXT_ANALYSIS,
        description=GET_TEXT_ANALYSIS,
        annotations=READ_ONLY_CRUD,
    )
