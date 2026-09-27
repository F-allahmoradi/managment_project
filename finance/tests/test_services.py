"""تست سرویس حساب و تراکنش: جمع با مانده و رد مبلغ صفر."""

from pathlib import Path
from decimal import Decimal
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.accounts import (
    account_transaction_sum,
    fetch_account,
    fetch_transactions,
    insert_account,
    insert_category,
    insert_transaction,
)
from errors.crud import INVALID_INPUT, InvalidInputError
from pydantic import ValidationError
from services.project import insert_project
from tests.conftest import (
    delete_temp_account,
    delete_temp_category,
    delete_temp_project,
    delete_temp_user,
    insert_temp_user,
    unique_account_name,
    unique_category_name,
    unique_project_name,
)
from validators.financial_transaction import validate_create_financial_transaction


class FinanceServiceTests(unittest.TestCase):
    """درج حساب و تراکنش روی Postgres بدون دفتر کل."""

    def test_income_and_expense_match_helper_balance(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-مالی")
        project_id = None
        account_id = None
        category_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("طراحی‌سایت"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            account_id = insert_account(
                {
                    "name": unique_account_name("بودجه پروژه طراحی سایت"),
                    "account_type": "بودجه پروژه",
                },
                actor_id=owner_id,
            )
            account = fetch_account(account_id)
            self.assertEqual(account["balance"], 0)
            self.assertEqual(account["account_type_name"], "بودجه پروژه")
            category_id = insert_category(
                {"name": unique_category_name("تجهیزات‌اضافی")},
                actor_id=owner_id,
            )
            insert_transaction(
                {
                    "account_id": account_id,
                    "amount": Decimal("10000000"),
                    "transaction_type": "دریافت",
                    "project_id": project_id,
                    "description": "تخصیص بودجه",
                },
                actor_id=owner_id,
            )
            insert_transaction(
                {
                    "account_id": account_id,
                    "amount": Decimal("8000000"),
                    "transaction_type": "پرداخت",
                    "project_id": project_id,
                    "category": "تجهیزات",
                    "description": "خرید تجهیزات",
                },
                actor_id=owner_id,
            )
            listed = fetch_transactions(
                limit=10,
                offset=0,
                project_id=project_id,
            )
            self.assertEqual(len(listed), 2)
            types = {row["transaction_type_name"] for row in listed}
            self.assertEqual(types, {"دریافت", "پرداخت"})
            amounts = {
                row["transaction_type_name"]: row["amount"] for row in listed
            }
            self.assertEqual(amounts["دریافت"], 10000000.0)
            self.assertEqual(amounts["پرداخت"], -8000000.0)
            after = fetch_account(account_id)
            total = account_transaction_sum(account_id)
            self.assertEqual(after["balance"], 2000000.0)
            self.assertEqual(float(total), after["balance"])
            with self.assertRaises(ValidationError):
                validate_create_financial_transaction(
                    {
                        "account_id": account_id,
                        "amount": 0,
                        "transaction_type": "پرداخت",
                    }
                )
            with self.assertRaises(InvalidInputError) as raised:
                insert_transaction(
                    {
                        "account_id": account_id,
                        "amount": Decimal("0"),
                        "transaction_type": "پرداخت",
                        "project_id": project_id,
                    },
                    actor_id=owner_id,
                )
            self.assertEqual(raised.exception.error_code, INVALID_INPUT)
        finally:
            if account_id is not None:
                delete_temp_account(account_id)
            if category_id is not None:
                delete_temp_category(category_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(owner_id)

    def test_transfer_is_a_single_row(self) -> None:
        owner_id = insert_temp_user(last_name="انتقال-مالی")
        account_id = None
        try:
            account_id = insert_account(
                {
                    "name": unique_account_name("صندوق"),
                    "account_type": "صندوق پروژه",
                },
                actor_id=owner_id,
            )
            insert_transaction(
                {
                    "account_id": account_id,
                    "amount": Decimal("-1500000"),
                    "transaction_type": "انتقال",
                    "description": "انتقال ساده یک‌ردیفی",
                },
                actor_id=owner_id,
            )
            listed = fetch_transactions(limit=10, offset=0, account_id=account_id)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["transaction_type_name"], "انتقال")
            self.assertEqual(listed[0]["amount"], -1500000.0)
            after = fetch_account(account_id)
            self.assertEqual(after["balance"], -1500000.0)
        finally:
            if account_id is not None:
                delete_temp_account(account_id)
            delete_temp_user(owner_id)


if __name__ == "__main__":
    unittest.main()
