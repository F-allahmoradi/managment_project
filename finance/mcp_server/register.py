"""ثبت ابزارهای حساب و تراکنش ساده روی سرور MCP.

حذف تراکنش و ابزار کامل نوع تراکنش در این گام ثبت نمی‌شوند.
"""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.financial_account.create_financial_account import (
    register as register_create_financial_account,
)
from mcp_server.tools.financial_account.get_financial_account import (
    register as register_get_financial_account,
)
from mcp_server.tools.financial_account.list_financial_accounts import (
    register as register_list_financial_accounts,
)
from mcp_server.tools.financial_category.create_financial_category import (
    register as register_create_financial_category,
)
from mcp_server.tools.financial_transaction.create_financial_transaction import (
    register as register_create_financial_transaction,
)
from mcp_server.tools.financial_transaction.list_financial_transactions import (
    register as register_list_financial_transactions,
)


def register_finance_tools(mcp: MCPServer) -> None:
    """ابزارهای حساب و تراکنش را روی سرور ثبت می‌کند."""
    setup_logging()
    register_create_financial_account(mcp)
    register_get_financial_account(mcp)
    register_list_financial_accounts(mcp)
    register_create_financial_transaction(mcp)
    register_list_financial_transactions(mcp)
    register_create_financial_category(mcp)
