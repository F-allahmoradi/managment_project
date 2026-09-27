"""ابزار MCP برای ساخت حساب مالی. مانده را کلاینت نمی‌نویسد."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import insert_account
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_FINANCIAL_ACCOUNT
from mcp_server.metadata import TITLE_CREATE_FINANCIAL_ACCOUNT, WRITE_FINANCE
from validators.financial_account import validate_create_financial_account


@logged_tool("create_financial_account")
def run_create_financial_account(**fields) -> dict:
    """مسیر کامل ساخت حساب را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Finance", "Create")
        parsed = validate_create_financial_account(fields)
        new_id = insert_account(parsed, actor_id=actor["id"])
        return format_success("حساب مالی ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_financial_account را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_financial_account",
        title=TITLE_CREATE_FINANCIAL_ACCOUNT,
        description=CREATE_FINANCIAL_ACCOUNT,
        annotations=WRITE_FINANCE,
    )
    def create_financial_account(
        name: str,
        account_type: Optional[str] = None,
        account_type_id: Optional[int] = None,
        is_active: bool = True,
    ) -> dict:
        """ابزار MCP: یک حساب در financial_accounts درج می‌کند."""
        return run_create_financial_account(
            name=name,
            account_type=account_type,
            account_type_id=account_type_id,
            is_active=is_active,
        )
