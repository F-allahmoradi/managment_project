"""ابزار MCP برای استخراج کلمهٔ کلیدی. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_keywords
from mcp_server.docstrings import EXTRACT_KEYWORDS
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_KEYWORDS
from mcp_server.tools.extract.common import make_extract_runner

run_extract_keywords = make_extract_runner("extract_keywords", extract_keywords)


def register(mcp: MCPServer) -> None:
    """ابزار extract_keywords را ثبت می‌کند."""

    @mcp.tool(
        name="extract_keywords",
        title=TITLE_EXTRACT_KEYWORDS,
        description=EXTRACT_KEYWORDS,
        annotations=READ_ONLY_NER,
    )
    def extract_keywords_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: عبارت کلیدی آزاد را از متن برمی‌دارد."""
        return run_extract_keywords(
            text=text,
            source_type=source_type,
            source_id=source_id,
        )
