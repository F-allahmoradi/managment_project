"""ابزار MCP برای نقل‌قول. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_quotes
from mcp_server.docstrings import EXTRACT_QUOTES
from mcp_server.metadata import READ_ONLY_NLP, TITLE_EXTRACT_QUOTES
from mcp_server.tools.extract.common import make_extract_runner

run_extract_quotes = make_extract_runner("extract_quotes", extract_quotes)


def register(mcp: MCPServer) -> None:
    """ابزار extract_quotes را ثبت می‌کند."""

    @mcp.tool(
        name="extract_quotes",
        title=TITLE_EXTRACT_QUOTES,
        description=EXTRACT_QUOTES,
        annotations=READ_ONLY_NLP,
    )
    def extract_quotes_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: نقل‌قول مستقیم و غیرمستقیم را برمی‌دارد."""
        return run_extract_quotes(
            text=text,
            source_type=source_type,
            source_id=source_id,
            context=context,
        )
