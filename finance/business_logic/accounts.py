"""دامنهٔ حساب و تراکنش ساده.

منبع حقیقت تراکنش است. ماندهٔ حساب از جمع تراکنش‌ها نوشته می‌شود.
حذف تراکنش نیست؛ جبران با ردیف بازگشت وجه است.
"""

from datetime import date
from decimal import Decimal

from errors.crud import (
    FinancialAccountNotFoundError,
    FinancialCategoryNotFoundError,
    InvalidInputError,
)
from logging_module import logged_step
from repository.db import run_query
from services.audit_log import ACTION_CREATE, record_audit_on
from services.project import fetch_project
from services.user import fetch_user

from business_logic.repository import (
    UNIQUE_MESSAGES,
    fetch_account_record,
    fetch_account_records,
    fetch_category_record,
    fetch_lookup_name,
    fetch_transaction_records,
    insert_account_on,
    insert_category_on,
    insert_transaction_on,
    resolve_lookup_id,
    sum_account_transactions_on,
)

INFLOW_TYPES = frozenset({"دریافت"})
OUTFLOW_TYPES = frozenset({"پرداخت"})


def _account_not_found(account_id: int) -> str:
    return f"حساب با شناسه {account_id} پیدا نشد"


def signed_amount(type_name: str, amount: Decimal) -> Decimal:
    """علامت مبلغ را برای دریافت و پرداخت اعمال می‌کند.

    دریافت همیشه مثبت ذخیره می‌شود، پرداخت همیشه منفی.
    انتقال و بازگشت وجه همان علامت ورودی را نگه می‌دارند.
    """
    if amount == 0:
        raise InvalidInputError("مبلغ صفر مجاز نیست")
    if type_name in INFLOW_TYPES:
        return abs(amount)
    if type_name in OUTFLOW_TYPES:
        return -abs(amount)
    return amount


def fetch_account(account_id: int) -> dict:
    """یک حساب را با شناسه می‌خواند."""
    row = fetch_account_record(account_id)
    if row is None:
        raise FinancialAccountNotFoundError(_account_not_found(account_id))
    return row


def fetch_accounts(limit: int, offset: int, is_active=None) -> list:
    """فهرست حساب‌ها را می‌خواند."""
    return fetch_account_records(limit, offset, is_active=is_active)


def insert_account(fields: dict, actor_id=None) -> int:
    """حساب جدید با ماندهٔ صفر می‌سازد."""
    type_id = resolve_lookup_id(
        "financial_account_types",
        fields.get("account_type_id"),
        fields.get("account_type"),
    )
    payload = {
        "name": fields["name"],
        "account_type_id": type_id,
        "is_active": fields.get("is_active", True),
    }

    def work(connection):
        new_id = insert_account_on(connection, payload)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "FinancialAccount",
            new_id,
            None,
            {"name": payload["name"], "account_type_id": type_id},
        )
        return new_id

    return run_query(work)


def fetch_transactions(
    limit: int,
    offset: int,
    account_id=None,
    project_id=None,
) -> list:
    """فهرست تراکنش‌ها را با فیلتر حساب یا پروژه می‌خواند."""
    if account_id is not None:
        fetch_account(account_id)
    if project_id is not None:
        fetch_project(project_id)
    return fetch_transaction_records(
        limit,
        offset,
        account_id=account_id,
        project_id=project_id,
    )


def insert_transaction(fields: dict, actor_id=None) -> int:
    """دریافت یا پرداخت را ثبت می‌کند و مانده را از جمع تراکنش‌ها می‌نویسد."""
    account = fetch_account(fields["account_id"])
    if account.get("is_active") is False:
        raise InvalidInputError("حساب غیرفعال است")
    project_id = fields.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
    user_id = fields.get("user_id")
    if user_id is not None:
        fetch_user(user_id)
    type_id = resolve_lookup_id(
        "transaction_types",
        fields.get("transaction_type_id"),
        fields.get("transaction_type"),
    )
    type_name = fields.get("transaction_type") or fetch_lookup_name(
        "transaction_types",
        type_id,
    )
    category_id = fields.get("category_id")
    if category_id is None and fields.get("category"):
        category_id = resolve_lookup_id(
            "financial_categories",
            None,
            fields.get("category"),
        )
    elif category_id is not None:
        category = fetch_category_record(category_id)
        if category is None:
            raise FinancialCategoryNotFoundError(
                f"دسته با شناسه {category_id} پیدا نشد"
            )
    amount = signed_amount(type_name, Decimal(str(fields["amount"])))
    transaction_date = fields.get("transaction_date") or date.today()
    payload = {
        "account_id": fields["account_id"],
        "project_id": project_id,
        "user_id": user_id,
        "category_id": category_id,
        "transaction_type_id": type_id,
        "amount": amount,
        "description": fields.get("description"),
        "transaction_date": transaction_date,
    }

    def work(connection):
        new_id = insert_transaction_on(connection, payload)
        if new_id is None:
            raise FinancialAccountNotFoundError(
                _account_not_found(fields["account_id"])
            )
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "FinancialTransaction",
            new_id,
            None,
            {
                "account_id": payload["account_id"],
                "amount": str(amount),
                "transaction_type_id": type_id,
                "project_id": project_id,
            },
        )
        return new_id

    return run_query(work)


def insert_category(fields: dict, actor_id=None) -> int:
    """دستهٔ مالی جدید می‌سازد."""
    payload = {
        "name": fields["name"],
        "description": fields.get("description"),
    }

    def work(connection):
        new_id = insert_category_on(connection, payload)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "FinancialCategory",
            new_id,
            None,
            {"name": payload["name"]},
        )
        return new_id

    return run_query(work, UNIQUE_MESSAGES)


def account_transaction_sum(account_id: int):
    """جمع تراکنش‌های حساب را جدا از فیلد مانده می‌خواند."""
    fetch_account(account_id)

    def work(connection):
        return sum_account_transactions_on(connection, account_id)

    return run_query(work)


insert_account = logged_step("insert")(insert_account)
fetch_account = logged_step("fetch")(fetch_account)
fetch_accounts = logged_step("fetch")(fetch_accounts)
insert_transaction = logged_step("insert")(insert_transaction)
fetch_transactions = logged_step("fetch")(fetch_transactions)
insert_category = logged_step("insert")(insert_category)
account_transaction_sum = logged_step("fetch")(account_transaction_sum)
