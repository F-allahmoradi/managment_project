"""ابزار MCP برای فهرست تراکنش‌ها با فیلتر پروژه یا حساب."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import fetch_transactions
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_FINANCIAL_TRANSACTIONS
from mcp_server.metadata import READ_ONLY_FINANCE, TITLE_LIST_FINANCIAL_TRANSACTIONS
from validators.financial_transaction import validate_list_financial_transactions


@logged_tool("list_financial_transactions")
def run_list_financial_transactions(
    account_id: Optional[int] = None,
    project_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست تراکنش‌ها را اجرا می‌کند."""
    try:
        require_permission("Finance", "Read")
        parsed = validate_list_financial_transactions(
            account_id=account_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
        records = fetch_transactions(
            parsed["limit"],
            parsed["offset"],
            account_id=parsed.get("account_id"),
            project_id=parsed.get("project_id"),
        )
        return format_success(
            "تراکنش‌های مالی فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_financial_transactions را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_financial_transactions",
        title=TITLE_LIST_FINANCIAL_TRANSACTIONS,
        description=LIST_FINANCIAL_TRANSACTIONS,
        annotations=READ_ONLY_FINANCE,
    )
    def list_financial_transactions(
        account_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: تراکنش‌ها را با فیلتر حساب یا پروژه می‌خواند."""
        return run_list_financial_transactions(
            account_id=account_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
