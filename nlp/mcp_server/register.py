"""ثبت ابزارهای فکت، نقل‌قول و قاب مسئله روی سرور MCP."""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.extract.extract_facts import register as register_extract_facts
from mcp_server.tools.extract.extract_frame import register as register_extract_frame
from mcp_server.tools.extract.extract_quotes import register as register_extract_quotes


def register_nlp_tools(mcp: MCPServer) -> None:
    """سه ابزار لایهٔ جدا را ثبت می‌کند."""
    setup_logging()
    register_extract_facts(mcp)
    register_extract_quotes(mcp)
    register_extract_frame(mcp)
