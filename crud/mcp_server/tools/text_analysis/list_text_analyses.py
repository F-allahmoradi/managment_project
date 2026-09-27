"""ابزار MCP برای فهرست تحلیل‌های متن ساخته‌شده توسط کاربر جاری."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_TEXT_ANALYSES
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_TEXT_ANALYSES
from services.text_analysis import fetch_text_analyses_for_actor
from validators.text_analysis import validate_list_text_analyses


@run_tool("list_text_analyses")
def run_list_text_analyses(
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست تحلیل‌های کاربر جاری را اجرا می‌کند."""
    actor = require_permission("TextAnalysis", "Read")
    parsed = validate_list_text_analyses(
        source_type=source_type,
        source_id=source_id,
        limit=limit,
        offset=offset,
    )
    records = fetch_text_analyses_for_actor(
        actor["id"],
        parsed["limit"],
        parsed["offset"],
        source_type=parsed.get("source_type"),
        source_id=parsed.get("source_id"),
    )
    return format_success(
        "تحلیل‌های متن فهرست شدند",
        records=records,
        limit=parsed["limit"],
        offset=parsed["offset"],
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_text_analyses را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_text_analyses",
        title=TITLE_LIST_TEXT_ANALYSES,
        description=LIST_TEXT_ANALYSES,
        annotations=READ_ONLY_CRUD,
    )
    def list_text_analyses(
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: تحلیل‌های ساخته‌شده توسط کاربر جاری را می‌خواند."""
        return run_list_text_analyses(
            source_type=source_type,
            source_id=source_id,
            limit=limit,
            offset=offset,
        )
