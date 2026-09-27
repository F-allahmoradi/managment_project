"""ابزار MCP برای ژانر / نوع پیام. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_discourse
from mcp_server.docstrings import EXTRACT_DISCOURSE
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_DISCOURSE
from mcp_server.tools.extract.common import make_extract_runner

run_extract_discourse = make_extract_runner(
    "extract_discourse",
    extract_discourse,
    extra_fields=("intended_meaning",),
)


def register(mcp: MCPServer) -> None:
    """ابزار extract_discourse را ثبت می‌کند."""

    @mcp.tool(
        name="extract_discourse",
        title=TITLE_EXTRACT_DISCOURSE,
        description=EXTRACT_DISCOURSE,
        annotations=READ_ONLY_NER,
    )
    def extract_discourse_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        intended_meaning: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: ژانر / نوع پیام را از متن برمی‌دارد."""
        return run_extract_discourse(
            text=text,
            source_type=source_type,
            source_id=source_id,
            intended_meaning=intended_meaning,
        )
