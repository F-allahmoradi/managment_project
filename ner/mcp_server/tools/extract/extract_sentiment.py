"""ابزار MCP برای قطبیت و هیجان. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_sentiment
from mcp_server.docstrings import EXTRACT_SENTIMENT
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_SENTIMENT
from mcp_server.tools.extract.common import make_extract_runner

run_extract_sentiment = make_extract_runner(
    "extract_sentiment",
    extract_sentiment,
    extra_fields=("intended_meaning",),
)


def register(mcp: MCPServer) -> None:
    """ابزار extract_sentiment را ثبت می‌کند."""

    @mcp.tool(
        name="extract_sentiment",
        title=TITLE_EXTRACT_SENTIMENT,
        description=EXTRACT_SENTIMENT,
        annotations=READ_ONLY_NER,
    )
    def extract_sentiment_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        intended_meaning: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: قطبیت و هیجان متن را برمی‌دارد."""
        return run_extract_sentiment(
            text=text,
            source_type=source_type,
            source_id=source_id,
            intended_meaning=intended_meaning,
        )
