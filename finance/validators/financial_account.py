"""اعتبارسنجی ورودی ابزارهای حساب مالی."""

from logging_module import logged_step


def validate_create_financial_account(fields: dict) -> dict:
    """ورودی ساخت حساب را با اسکیما بررسی می‌کند."""
    from schemas.finance.financial_account import CreateFinancialAccountInput

    return CreateFinancialAccountInput(**fields).model_dump()


def validate_get_financial_account(account_id: int) -> int:
    """شناسه خواندن حساب را با اسکیما بررسی می‌کند."""
    from schemas.finance.financial_account import GetFinancialAccountInput

    return GetFinancialAccountInput(id=account_id).id


def validate_list_financial_accounts(is_active=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر فعال بودن فهرست حساب را بررسی می‌کند."""
    from schemas.finance.financial_account import ListFinancialAccountsInput

    payload = {}
    if is_active is not None:
        payload["is_active"] = is_active
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return ListFinancialAccountsInput(**payload).model_dump()


validate_create_financial_account = logged_step("validate")(
    validate_create_financial_account
)
validate_get_financial_account = logged_step("validate")(validate_get_financial_account)
validate_list_financial_accounts = logged_step("validate")(
    validate_list_financial_accounts
)
