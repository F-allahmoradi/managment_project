"""تست ثبت ابزار مالی و پاکت JSON روی دیتابیس واقعی."""

from pathlib import Path
import asyncio
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import (
    FINANCIAL_ACCOUNT_NOT_FOUND,
    INVALID_INPUT,
    PERMISSION_DENIED,
    format_error,
    format_success,
)
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_CREATE_FINANCIAL_ACCOUNT,
    TITLE_LIST_FINANCIAL_TRANSACTIONS,
    WRITE_FINANCE,
)
from mcp_server.register import register_finance_tools
from mcp_server.tools.financial_account.create_financial_account import (
    run_create_financial_account,
)
from mcp_server.tools.financial_account.get_financial_account import (
    run_get_financial_account,
)
from mcp_server.tools.financial_account.list_financial_accounts import (
    run_list_financial_accounts,
)
from mcp_server.tools.financial_category.create_financial_category import (
    run_create_financial_category,
)
from mcp_server.tools.financial_transaction.create_financial_transaction import (
    run_create_financial_transaction,
)
from mcp_server.tools.financial_transaction.list_financial_transactions import (
    run_list_financial_transactions,
)
from services.project import insert_project
from tests.conftest import (
    bind_actor_as_role,
    delete_temp_account,
    delete_temp_category,
    delete_temp_project,
    unique_account_name,
    unique_category_name,
    unique_project_name,
)


_REGISTERED_TOOLS = {
    "create_financial_account",
    "get_financial_account",
    "list_financial_accounts",
    "create_financial_transaction",
    "list_financial_transactions",
    "create_financial_category",
}


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت فقط ابزارهای حساب و تراکنش را بررسی می‌کند."""

    def test_metadata_names_management_finance(self) -> None:
        self.assertEqual(SERVER_NAME, "management-finance")
        self.assertEqual(SERVER_TITLE, "مالی سامانه مدیریت")

    def test_register_adds_finance_tools_only(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_finance_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(names, _REGISTERED_TOOLS)
        self.assertNotIn("delete_financial_transaction", names)
        self.assertNotIn("create_transaction_type", names)
        self.assertNotIn("create_performance_action", names)

    def test_server_module_lists_registered_tools(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(mcp.name, SERVER_NAME)
        names = {tool.name for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(names, _REGISTERED_TOOLS)


class ErrorEnvelopeTests(unittest.TestCase):
    def test_success_envelope(self) -> None:
        payload = format_success("ثبت شد", id=7)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["id"], 7)

    def test_unknown_maps_to_database_error(self) -> None:
        payload = format_error(RuntimeError("boom"))
        self.assertEqual(payload["error_code"], "DATABASE_ERROR")


class FinanceToolTests(unittest.TestCase):
    """حساب پروژه، دریافت، پرداخت، فهرست، مانده، و رد مبلغ صفر."""

    def test_create_account_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_financial_account"]
        self.assertEqual(tool.title, TITLE_CREATE_FINANCIAL_ACCOUNT)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertEqual(
            tool.annotations.read_only_hint,
            WRITE_FINANCE.read_only_hint,
        )
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("name", required)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("account_type", properties)
        self.assertNotIn("balance", properties)
        tx_tool = by_name["create_financial_transaction"]
        tx_required = set(tx_tool.input_schema.get("required") or [])
        self.assertIn("account_id", tx_required)
        self.assertIn("amount", tx_required)
        self.assertNotIn("delete_financial_transaction", by_name)
        list_tool = by_name["list_financial_transactions"]
        self.assertEqual(list_tool.title, TITLE_LIST_FINANCIAL_TRANSACTIONS)
        self.assertTrue(list_tool.annotations.read_only_hint)

    def test_project_account_income_expense_and_zero_rejected(self) -> None:
        ali = bind_actor_as_role("مسئول مالی")
        project_id = None
        account_id = None
        category_id = None
        outsider = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سایت"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=ali.user_id,
            )
            created = run_create_financial_account(
                name=unique_account_name("بودجه پروژه طراحی سایت"),
                account_type="بودجه پروژه",
            )
            self.assertEqual(created["status"], "success")
            account_id = created["id"]
            fetched = run_get_financial_account(id=account_id)
            self.assertEqual(fetched["status"], "success")
            self.assertEqual(fetched["account_type_name"], "بودجه پروژه")
            self.assertEqual(fetched["balance"], 0)
            income = run_create_financial_transaction(
                account_id=account_id,
                amount=10_000_000,
                transaction_type="دریافت",
                project_id=project_id,
                description="تخصیص بودجه",
            )
            self.assertEqual(income["status"], "success")
            expense = run_create_financial_transaction(
                account_id=account_id,
                amount=8_000_000,
                transaction_type="پرداخت",
                project_id=project_id,
                category="تجهیزات",
                description="خرید تجهیزات",
            )
            self.assertEqual(expense["status"], "success")
            listed = run_list_financial_transactions(
                project_id=project_id,
                limit=50,
            )
            self.assertEqual(listed["status"], "success")
            self.assertEqual(len(listed["records"]), 2)
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(income["id"], ids)
            self.assertIn(expense["id"], ids)
            by_type = {
                row["transaction_type_name"]: row for row in listed["records"]
            }
            self.assertEqual(by_type["دریافت"]["amount"], 10_000_000)
            self.assertEqual(by_type["پرداخت"]["amount"], -8_000_000)
            self.assertEqual(by_type["پرداخت"]["category_name"], "تجهیزات")
            after = run_get_financial_account(id=account_id)
            self.assertEqual(after["balance"], 2_000_000)
            total = sum(row["amount"] for row in listed["records"])
            self.assertEqual(total, after["balance"])
            zero = run_create_financial_transaction(
                account_id=account_id,
                amount=0,
                transaction_type="پرداخت",
                project_id=project_id,
            )
            self.assertEqual(zero["status"], "error")
            self.assertEqual(zero["error_code"], INVALID_INPUT)
            category = run_create_financial_category(
                name=unique_category_name("هزینه ابری")
            )
            self.assertEqual(category["status"], "success")
            category_id = category["id"]
            refund = run_create_financial_transaction(
                account_id=account_id,
                amount=1_000_000,
                transaction_type="بازگشت وجه",
                project_id=project_id,
                description="جبران بخشی از پرداخت",
            )
            self.assertEqual(refund["status"], "success")
            listed_again = run_list_financial_transactions(
                account_id=account_id,
                limit=50,
            )
            self.assertEqual(len(listed_again["records"]), 3)
            self.assertIn(
                "بازگشت وجه",
                {row["transaction_type_name"] for row in listed_again["records"]},
            )
            outsider = bind_actor_as_role("کاربر")
            denied = run_create_financial_account(
                name=unique_account_name("بدون‌مجوز"),
                account_type="حساب سازمان",
            )
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            hidden = run_list_financial_accounts(limit=50)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
        finally:
            if outsider is not None:
                outsider.close()
            if account_id is not None:
                delete_temp_account(account_id)
            if category_id is not None:
                delete_temp_category(category_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_missing_account_is_not_found(self) -> None:
        ali = bind_actor_as_role("مسئول مالی")
        try:
            missing = run_get_financial_account(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], FINANCIAL_ACCOUNT_NOT_FOUND)
        finally:
            ali.close()


if __name__ == "__main__":
    unittest.main()
