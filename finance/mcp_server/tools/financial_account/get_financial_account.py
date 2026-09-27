"""ابزار MCP برای خواندن یک حساب مالی با شناسه."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import fetch_account
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import GET_FINANCIAL_ACCOUNT
from mcp_server.metadata import READ_ONLY_FINANCE, TITLE_GET_FINANCIAL_ACCOUNT
from validators.financial_account import validate_get_financial_account


@logged_tool("get_financial_account")
def run_get_financial_account(id: int) -> dict:
    """مسیر کامل خواندن حساب را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        require_permission("Finance", "Read")
        account_id = validate_get_financial_account(id)
        account = fetch_account(account_id)
        return format_success("حساب مالی خوانده شد", **account)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار get_financial_account را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="get_financial_account",
        title=TITLE_GET_FINANCIAL_ACCOUNT,
        description=GET_FINANCIAL_ACCOUNT,
        annotations=READ_ONLY_FINANCE,
    )
    def get_financial_account(id: int) -> dict:
        """ابزار MCP: یک حساب را با شناسه می‌خواند."""
        return run_get_financial_account(id=id)
