"""ثبت ابزارهای امبدینگ و جستجو روی سرور MCP."""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.index_pending_analyses import (
    register as register_index_pending_analyses,
)
from mcp_server.tools.index_text_analysis import (
    register as register_index_text_analysis,
)
from mcp_server.tools.search_similar import register as register_search_similar


def register_embedding_tools(mcp: MCPServer) -> None:
    """ابزار ایندکس و جستجوی مشابه را ثبت می‌کند."""
    setup_logging()
    register_index_text_analysis(mcp)
    register_index_pending_analyses(mcp)
    register_search_similar(mcp)
