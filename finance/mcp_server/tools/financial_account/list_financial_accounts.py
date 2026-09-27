"""ابزار MCP برای فهرست حساب‌های مالی."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import fetch_accounts
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_FINANCIAL_ACCOUNTS
from mcp_server.metadata import READ_ONLY_FINANCE, TITLE_LIST_FINANCIAL_ACCOUNTS
from validators.financial_account import validate_list_financial_accounts


@logged_tool("list_financial_accounts")
def run_list_financial_accounts(
    is_active: Optional[bool] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """مسیر کامل فهرست حساب‌ها را اجرا می‌کند."""
    try:
        require_permission("Finance", "Read")
        parsed = validate_list_financial_accounts(
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        records = fetch_accounts(
            parsed["limit"],
            parsed["offset"],
            is_active=parsed.get("is_active"),
        )
        return format_success(
            "حساب‌های مالی فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_financial_accounts را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_financial_accounts",
        title=TITLE_LIST_FINANCIAL_ACCOUNTS,
        description=LIST_FINANCIAL_ACCOUNTS,
        annotations=READ_ONLY_FINANCE,
    )
    def list_financial_accounts(
        is_active: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """ابزار MCP: حساب‌های مالی را می‌خواند."""
        return run_list_financial_accounts(
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
