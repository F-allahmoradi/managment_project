"""تست اعتبارسنجی مبلغ صفر و نوع حساب بدون دیتابیس."""

from pathlib import Path
from decimal import Decimal
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.accounts import signed_amount
from errors.crud import INVALID_INPUT, InvalidInputError
from pydantic import ValidationError
from schemas.finance.financial_transaction import CreateFinancialTransactionInput
from validators.financial_transaction import validate_create_financial_transaction


class FinanceValidatorTests(unittest.TestCase):
    """مبلغ صفر و علامت دریافت/پرداخت را بدون Postgres می‌سنجد."""

    def test_zero_amount_is_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            CreateFinancialTransactionInput(
                account_id=1,
                amount=0,
                transaction_type="پرداخت",
            )
        with self.assertRaises(ValidationError):
            validate_create_financial_transaction(
                {
                    "account_id": 1,
                    "amount": 0,
                    "transaction_type": "دریافت",
                }
            )

    def test_signed_amount_for_income_and_expense(self) -> None:
        self.assertEqual(signed_amount("دریافت", Decimal("8000000")), Decimal("8000000"))
        self.assertEqual(signed_amount("پرداخت", Decimal("8000000")), Decimal("-8000000"))
        self.assertEqual(signed_amount("پرداخت", Decimal("-8000000")), Decimal("-8000000"))
        self.assertEqual(signed_amount("انتقال", Decimal("-1000")), Decimal("-1000"))
        with self.assertRaises(InvalidInputError) as raised:
            signed_amount("دریافت", Decimal("0"))
        self.assertEqual(raised.exception.error_code, INVALID_INPUT)


if __name__ == "__main__":
    unittest.main()
