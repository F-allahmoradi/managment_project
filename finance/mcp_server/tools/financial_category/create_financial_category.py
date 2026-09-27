"""ابزار MCP برای افزودن دستهٔ مالی. نوع تراکنش ابزار کامل ندارد."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.accounts import insert_category
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_FINANCIAL_CATEGORY
from mcp_server.metadata import TITLE_CREATE_FINANCIAL_CATEGORY, WRITE_FINANCE
from validators.financial_category import validate_create_financial_category


@logged_tool("create_financial_category")
def run_create_financial_category(**fields) -> dict:
    """مسیر کامل افزودن دسته را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Finance", "Create")
        parsed = validate_create_financial_category(fields)
        new_id = insert_category(parsed, actor_id=actor["id"])
        return format_success("دسته مالی ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_financial_category را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_financial_category",
        title=TITLE_CREATE_FINANCIAL_CATEGORY,
        description=CREATE_FINANCIAL_CATEGORY,
        annotations=WRITE_FINANCE,
    )
    def create_financial_category(
        name: str,
        description: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف financial_categories درج می‌کند."""
        return run_create_financial_category(
            name=name,
            description=description,
        )
