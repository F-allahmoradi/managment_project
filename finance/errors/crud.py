"""خطاهای معنایی مالی با همان پاکت JSON لایهٔ CRUD.

کلاس‌های مشترک از crud/errors/crud.py بارگذاری می‌شوند تا
auth و سرویس‌های کراد همان error_code را ببینند.
"""

import importlib.util
from pathlib import Path

_CRUD_ERRORS_PATH = Path(__file__).resolve().parents[2] / "crud" / "errors" / "crud.py"
_spec = importlib.util.spec_from_file_location(
    "_shared_crud_errors",
    _CRUD_ERRORS_PATH,
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)

CrudError = _mod.CrudError
format_error = _mod.format_error
format_success = _mod.format_success

FINANCIAL_ACCOUNT_NOT_FOUND = "FINANCIAL_ACCOUNT_NOT_FOUND"
FINANCIAL_TRANSACTION_NOT_FOUND = "FINANCIAL_TRANSACTION_NOT_FOUND"
FINANCIAL_CATEGORY_NOT_FOUND = "FINANCIAL_CATEGORY_NOT_FOUND"


class FinancialAccountNotFoundError(CrudError):
    """حساب با شناسه داده‌شده در financial_accounts نیست."""

    error_code = FINANCIAL_ACCOUNT_NOT_FOUND


class FinancialTransactionNotFoundError(CrudError):
    """تراکنش با شناسه داده‌شده در financial_transactions نیست."""

    error_code = FINANCIAL_TRANSACTION_NOT_FOUND


class FinancialCategoryNotFoundError(CrudError):
    """دسته با شناسه داده‌شده در financial_categories نیست."""

    error_code = FINANCIAL_CATEGORY_NOT_FOUND
