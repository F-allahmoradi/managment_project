"""ابزار MCP برای جستجوی موارد مشابه از بردار خام و فکت."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.searcher import search_similar
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import SEARCH_SIMILAR
from mcp_server.metadata import READ_ONLY_EMBEDDING, TITLE_SEARCH_SIMILAR
from validators.search import validate_search_similar


@logged_tool("search_similar")
def run_search_similar(
    query: str,
    kinds: Optional[list] = None,
    source_type: Optional[str] = None,
    limit: int = 8,
) -> dict:
    """مسیر کامل جستجوی مشابه را اجرا می‌کند."""
    try:
        actor = require_permission("TextAnalysis", "Read")
        parsed = validate_search_similar(
            query=query,
            kinds=kinds,
            source_type=source_type,
            limit=limit,
        )
        found = search_similar(
            actor["id"],
            parsed["query"],
            kinds=parsed.get("kinds"),
            source_type=parsed.get("source_type"),
            limit=parsed["limit"],
        )
        return format_success("موارد مشابه پیدا شد", **found)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار search_similar را ثبت می‌کند."""

    @mcp.tool(
        name="search_similar",
        title=TITLE_SEARCH_SIMILAR,
        description=SEARCH_SIMILAR,
        annotations=READ_ONLY_EMBEDDING,
    )
    def search_similar_tool(
        query: str,
        kinds: Optional[list] = None,
        source_type: Optional[str] = None,
        limit: int = 8,
    ) -> dict:
        """ابزار MCP: موارد مشابه سؤال را از بردارها می‌آورد."""
        return run_search_similar(
            query=query,
            kinds=kinds,
            source_type=source_type,
            limit=limit,
        )
