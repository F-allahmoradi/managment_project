"""ابزار MCP برای ثبت دریافت یا پرداخت روی حساب.

حذف تراکنش ثبت نمی‌شود. مانده از جمع تراکنش‌ها می‌آید.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import insert_transaction
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_FINANCIAL_TRANSACTION
from mcp_server.metadata import TITLE_CREATE_FINANCIAL_TRANSACTION, WRITE_FINANCE
from validators.financial_transaction import validate_create_financial_transaction


@logged_tool("create_financial_transaction")
def run_create_financial_transaction(**fields) -> dict:
    """مسیر کامل ثبت تراکنش را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Finance", "Create")
        parsed = validate_create_financial_transaction(fields)
        new_id = insert_transaction(parsed, actor_id=actor["id"])
        return format_success("تراکنش مالی ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_financial_transaction را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_financial_transaction",
        title=TITLE_CREATE_FINANCIAL_TRANSACTION,
        description=CREATE_FINANCIAL_TRANSACTION,
        annotations=WRITE_FINANCE,
    )
    def create_financial_transaction(
        account_id: int,
        amount: float,
        transaction_type: Optional[str] = None,
        transaction_type_id: Optional[int] = None,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        transaction_date: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف financial_transactions درج می‌کند."""
        return run_create_financial_transaction(
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            transaction_type_id=transaction_type_id,
            project_id=project_id,
            user_id=user_id,
            category=category,
            category_id=category_id,
            description=description,
            transaction_date=transaction_date,
        )
