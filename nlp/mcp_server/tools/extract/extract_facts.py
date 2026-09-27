"""ابزار MCP برای فکت مقید به شاهد. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_facts
from mcp_server.docstrings import EXTRACT_FACTS
from mcp_server.metadata import READ_ONLY_NLP, TITLE_EXTRACT_FACTS
from mcp_server.tools.extract.common import make_extract_runner

run_extract_facts = make_extract_runner("extract_facts", extract_facts)


def register(mcp: MCPServer) -> None:
    """ابزار extract_facts را ثبت می‌کند."""

    @mcp.tool(
        name="extract_facts",
        title=TITLE_EXTRACT_FACTS,
        description=EXTRACT_FACTS,
        annotations=READ_ONLY_NLP,
    )
    def extract_facts_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: فکت و صراحت را از متن برمی‌دارد."""
        return run_extract_facts(
            text=text,
            source_type=source_type,
            source_id=source_id,
            context=context,
        )
