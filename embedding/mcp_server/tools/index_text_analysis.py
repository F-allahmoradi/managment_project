"""ابزار MCP برای برداری‌کردن یک تحلیل ذخیره‌شده."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.indexer import index_analysis
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import INDEX_TEXT_ANALYSIS
from mcp_server.metadata import TITLE_INDEX_TEXT_ANALYSIS, WRITE_EMBEDDING
from validators.search import validate_index_text_analysis


@logged_tool("index_text_analysis")
def run_index_text_analysis(analysis_id: int) -> dict:
    """مسیر کامل ایندکس یک تحلیل را اجرا می‌کند."""
    try:
        actor = require_permission("TextAnalysis", "Create")
        parsed_id = validate_index_text_analysis(analysis_id)
        stored = index_analysis(parsed_id, actor["id"])
        return format_success("تحلیل متن برداری شد", **stored)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار index_text_analysis را ثبت می‌کند."""

    @mcp.tool(
        name="index_text_analysis",
        title=TITLE_INDEX_TEXT_ANALYSIS,
        description=INDEX_TEXT_ANALYSIS,
        annotations=WRITE_EMBEDDING,
    )
    def index_text_analysis(analysis_id: int) -> dict:
        """ابزار MCP: متن خام و فکت‌های یک تحلیل را امبد می‌کند."""
        return run_index_text_analysis(analysis_id=analysis_id)
