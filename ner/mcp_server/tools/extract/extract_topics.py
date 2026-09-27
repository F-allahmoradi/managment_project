"""ابزار MCP برای طبقه‌بندی موضوع. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_topics
from mcp_server.docstrings import EXTRACT_TOPICS
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_TOPICS
from mcp_server.tools.extract.common import make_extract_runner

run_extract_topics = make_extract_runner("extract_topics", extract_topics)


def register(mcp: MCPServer) -> None:
    """ابزار extract_topics را ثبت می‌کند."""

    @mcp.tool(
        name="extract_topics",
        title=TITLE_EXTRACT_TOPICS,
        description=EXTRACT_TOPICS,
        annotations=READ_ONLY_NER,
    )
    def extract_topics_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: موضوع کاتالوگ یا موضوع فهمیده‌شدهٔ خارج از درخت را برمی‌دارد."""
        return run_extract_topics(
            text=text,
            source_type=source_type,
            source_id=source_id,
        )
