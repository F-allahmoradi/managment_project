"""ابزار MCP برای قاب مسئله. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_frame
from mcp_server.docstrings import EXTRACT_FRAME
from mcp_server.metadata import READ_ONLY_NLP, TITLE_EXTRACT_FRAME
from mcp_server.tools.extract.common import make_extract_runner

run_extract_frame = make_extract_runner("extract_frame", extract_frame)


def register(mcp: MCPServer) -> None:
    """ابزار extract_frame را ثبت می‌کند."""

    @mcp.tool(
        name="extract_frame",
        title=TITLE_EXTRACT_FRAME,
        description=EXTRACT_FRAME,
        annotations=READ_ONLY_NLP,
    )
    def extract_frame_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: عنوان، واحد، فرآیند و محدوده را برمی‌دارد."""
        return run_extract_frame(
            text=text,
            source_type=source_type,
            source_id=source_id,
            context=context,
        )
