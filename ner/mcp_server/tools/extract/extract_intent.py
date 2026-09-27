"""ابزار MCP برای نیت گوینده. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_intent
from mcp_server.docstrings import EXTRACT_INTENT
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_INTENT
from mcp_server.tools.extract.common import make_extract_runner

run_extract_intent = make_extract_runner(
    "extract_intent",
    extract_intent,
    extra_fields=("intended_meaning",),
)


def register(mcp: MCPServer) -> None:
    """ابزار extract_intent را ثبت می‌کند."""

    @mcp.tool(
        name="extract_intent",
        title=TITLE_EXTRACT_INTENT,
        description=EXTRACT_INTENT,
        annotations=READ_ONLY_NER,
    )
    def extract_intent_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        intended_meaning: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: نیت / مسیر رسیدگی را از متن برمی‌دارد."""
        return run_extract_intent(
            text=text,
            source_type=source_type,
            source_id=source_id,
            intended_meaning=intended_meaning,
        )
