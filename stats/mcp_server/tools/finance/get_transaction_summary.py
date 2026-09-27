"""ابزار MCP برای جمع تراکنش‌های قابل‌مشاهده."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from business_logic.analyst import transaction_summary
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_TRANSACTION_SUMMARY
from mcp_server.metadata import READ_ONLY_STATS, TITLE_GET_TRANSACTION_SUMMARY
from mcp_server.scope import actor_for_optional_project
from schemas.input import validate_transaction_filter


@logged_tool("get_transaction_summary")
def run_get_transaction_summary(
    project_id: Optional[int] = None,
    account_id: Optional[int] = None,
) -> dict:
    """مسیر کامل خلاصه تراکنش را اجرا می‌کند."""
    try:
        actor, scoped_project = actor_for_optional_project(
            "Finance",
            "Read",
            project_id,
        )
        parsed = validate_transaction_filter(
            project_id=scoped_project,
            account_id=account_id,
        )
        payload = transaction_summary(
            actor["id"],
            parsed.get("project_id"),
            parsed.get("account_id"),
        )
        return format_success("خلاصه تراکنش‌ها محاسبه شد", **payload)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_transaction_summary را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_transaction_summary",
        title=TITLE_GET_TRANSACTION_SUMMARY,
        description=GET_TRANSACTION_SUMMARY,
        annotations=READ_ONLY_STATS,
    )
    def get_transaction_summary(
        project_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: جمع دریافت و پرداخت را می‌خواند."""
        return run_get_transaction_summary(
            project_id=project_id,
            account_id=account_id,
        )
