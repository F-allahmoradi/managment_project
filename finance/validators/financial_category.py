"""اعتبارسنجی ورودی افزودن دستهٔ مالی."""

from logging_module import logged_step


def validate_create_financial_category(fields: dict) -> dict:
    """ورودی افزودن دسته را با اسکیما بررسی می‌کند."""
    from schemas.finance.financial_category import CreateFinancialCategoryInput

    return CreateFinancialCategoryInput(**fields).model_dump()


validate_create_financial_category = logged_step("validate")(
    validate_create_financial_category
)
