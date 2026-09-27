"""اعتبارسنجی ورودی ابزارهای تراکنش مالی."""

from logging_module import logged_step


def validate_create_financial_transaction(fields: dict) -> dict:
    """ورودی ثبت تراکنش را با اسکیما بررسی می‌کند."""
    from schemas.finance.financial_transaction import CreateFinancialTransactionInput

    return CreateFinancialTransactionInput(**fields).model_dump()


def validate_list_financial_transactions(
    account_id=None,
    project_id=None,
    limit=None,
    offset=None,
) -> dict:
    """فیلتر حساب یا پروژه و صفحه‌بندی فهرست تراکنش را بررسی می‌کند."""
    from schemas.finance.financial_transaction import ListFinancialTransactionsInput

    payload = {}
    if account_id is not None:
        payload["account_id"] = account_id
    if project_id is not None:
        payload["project_id"] = project_id
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListFinancialTransactionsInput(**payload).model_dump()


validate_create_financial_transaction = logged_step("validate")(
    validate_create_financial_transaction
)
validate_list_financial_transactions = logged_step("validate")(
    validate_list_financial_transactions
)
