"""ثبت ابزارهای استخراج روی سرور MCP."""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.extract.extract_discourse import (
    register as register_extract_discourse,
)
from mcp_server.tools.extract.extract_entities import register as register_extract_entities
from mcp_server.tools.extract.extract_intent import register as register_extract_intent
from mcp_server.tools.extract.extract_keywords import register as register_extract_keywords
from mcp_server.tools.extract.extract_rhetoric import (
    register as register_extract_rhetoric,
)
from mcp_server.tools.extract.extract_sentiment import (
    register as register_extract_sentiment,
)
from mcp_server.tools.extract.extract_topics import register as register_extract_topics


def register_ner_tools(mcp: MCPServer) -> None:
    """هفت ابزار لایهٔ جدا را ثبت می‌کند."""
    setup_logging()
    register_extract_entities(mcp)
    register_extract_keywords(mcp)
    register_extract_topics(mcp)
    register_extract_sentiment(mcp)
    register_extract_discourse(mcp)
    register_extract_intent(mcp)
    register_extract_rhetoric(mcp)
