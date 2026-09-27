"""ابزار MCP برای صنعت بیان. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_rhetoric
from mcp_server.docstrings import EXTRACT_RHETORIC
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_RHETORIC
from mcp_server.tools.extract.common import make_extract_runner

run_extract_rhetoric = make_extract_runner("extract_rhetoric", extract_rhetoric)


def register(mcp: MCPServer) -> None:
    """ابزار extract_rhetoric را ثبت می‌کند."""

    @mcp.tool(
        name="extract_rhetoric",
        title=TITLE_EXTRACT_RHETORIC,
        description=EXTRACT_RHETORIC,
        annotations=READ_ONLY_NER,
    )
    def extract_rhetoric_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: صنعت بیان و معنای مقصود را از متن برمی‌دارد."""
        return run_extract_rhetoric(
            text=text,
            source_type=source_type,
            source_id=source_id,
        )
