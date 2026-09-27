"""ابزار MCP برای ایندکس تحلیل‌هایی که هنوز بردار ندارند."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.indexer import index_pending
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import INDEX_PENDING_ANALYSES
from mcp_server.metadata import TITLE_INDEX_PENDING_ANALYSES, WRITE_EMBEDDING
from validators.search import validate_index_pending


@logged_tool("index_pending_analyses")
def run_index_pending_analyses(limit: int = 20) -> dict:
    """مسیر کامل ایندکس باقی‌مانده را اجرا می‌کند."""
    try:
        actor = require_permission("TextAnalysis", "Create")
        parsed_limit = validate_index_pending(limit)
        stored = index_pending(actor["id"], parsed_limit)
        return format_success("تحلیل‌های باقی‌مانده برداری شدند", **stored)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار index_pending_analyses را ثبت می‌کند."""

    @mcp.tool(
        name="index_pending_analyses",
        title=TITLE_INDEX_PENDING_ANALYSES,
        description=INDEX_PENDING_ANALYSES,
        annotations=WRITE_EMBEDDING,
    )
    def index_pending_analyses(limit: int = 20) -> dict:
        """ابزار MCP: تحلیل‌های بدون بردار را امبد می‌کند."""
        return run_index_pending_analyses(limit=limit)
