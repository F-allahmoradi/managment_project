"""ابزار MCP برای استخراج موجودیت از متن پروژه. INSERT نیست."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.extractor import extract_entities
from mcp_server.docstrings import EXTRACT_ENTITIES
from mcp_server.metadata import READ_ONLY_NER, TITLE_EXTRACT_ENTITIES
from mcp_server.tools.extract.common import make_extract_runner

run_extract_entities = make_extract_runner("extract_entities", extract_entities)


def register(mcp: MCPServer) -> None:
    """ابزار extract_entities را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="extract_entities",
        title=TITLE_EXTRACT_ENTITIES,
        description=EXTRACT_ENTITIES,
        annotations=READ_ONLY_NER,
    )
    def extract_entities_tool(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: موجودیت نام‌دار را از متن استخراج می‌کند."""
        return run_extract_entities(
            text=text,
            source_type=source_type,
            source_id=source_id,
        )
