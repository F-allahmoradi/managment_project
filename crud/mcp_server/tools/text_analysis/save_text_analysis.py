"""ابزار MCP برای ذخیره خروجی استخراج در جداول تحلیل متن.

وضعیت موجودیت‌ها پیشنهادی است تا نمایش و بررسی دقت جدا بماند.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import SAVE_TEXT_ANALYSIS
from mcp_server.metadata import TITLE_SAVE_TEXT_ANALYSIS, WRITE_CRUD
from services.text_analysis import insert_text_analysis
from validators.text_analysis import validate_save_text_analysis


@run_tool("save_text_analysis")
def run_save_text_analysis(**fields) -> dict:
    """مسیر کامل ذخیره تحلیل متن را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("TextAnalysis", "Create")
    parsed = validate_save_text_analysis(fields)
    stored = insert_text_analysis(parsed, created_by=actor["id"])
    return format_success("تحلیل متن با وضعیت پیشنهادی ثبت شد", **stored)


def register(mcp: MCPServer) -> None:
    """ابزار save_text_analysis را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="save_text_analysis",
        title=TITLE_SAVE_TEXT_ANALYSIS,
        description=SAVE_TEXT_ANALYSIS,
        annotations=WRITE_CRUD,
    )
    def save_text_analysis(
        source_type: str,
        source_id: Optional[int] = None,
        text: Optional[str] = None,
        model: Optional[str] = None,
        mentions: Optional[list] = None,
        keywords: Optional[list] = None,
        topics: Optional[list] = None,
        sentiment: Optional[dict] = None,
        emotions: Optional[list] = None,
        discourses: Optional[list] = None,
        intents: Optional[list] = None,
        rhetorics: Optional[list] = None,
        facts: Optional[list] = None,
        quotes: Optional[list] = None,
        intended_meaning: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: خروجی NER را در جداول تحلیل با وضعیت پیشنهادی می‌نویسد."""
        payload = {
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "mentions": mentions or [],
            "keywords": keywords or [],
            "topics": topics or [],
            "sentiment": sentiment,
            "emotions": emotions or [],
            "discourses": discourses or [],
            "intents": intents or [],
            "rhetorics": rhetorics or [],
            "facts": facts or [],
            "quotes": quotes or [],
            "intended_meaning": intended_meaning,
        }
        if model is not None:
            payload["model"] = model
        return run_save_text_analysis(**payload)
