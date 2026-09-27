"""سرویس تشویق و تنبیه؛ جدا از User و جدا از ابزارهای finance.

امتیاز در performance_scores ساخته می‌شود. مبلغ نقدی همان لحظه
یک تراکنش با نوع پاداش یا جریمه می‌سازد و شناسه‌اش روی اقدام می‌ماند.
"""

from decimal import Decimal

from errors.crud import InvalidInputError, PerformanceActionNotFoundError
from logging_module import logged_step
from repository import (
    fetch_financial_account_record,
    fetch_first,
    fetch_performance_action_record,
    fetch_performance_action_records,
    insert_cash_transaction_on,
    insert_row_on,
    resolve_lookup_id,
    run_query,
    sum_performance_action_scores_for_user,
    sum_performance_scores_for_user,
)
from services.audit_log import ACTION_CREATE, record_audit_on
from services.project import fetch_project
from services.user import fetch_user

SCORE_SOURCE = "PerformanceAction"
REWARD_CATEGORY = "REWARD"
PENALTY_CATEGORY = "PENALTY"
TX_TYPE_REWARD = "پاداش"
TX_TYPE_PENALTY = "جریمه"


def _not_found_message(row_id: int) -> str:
    return f"اقدام عملکرد با شناسه {row_id} پیدا نشد"


def _require_reason(reason) -> str:
    if reason is None or not str(reason).strip():
        raise InvalidInputError("دلیل اقدام خالی مجاز نیست")
    return reason


def _resolve_action_type(fields: dict) -> dict:
    type_id = resolve_lookup_id(
        "performance_action_types",
        fields.get("action_type_id") or fields.get("type_id"),
        fields.get("action_type"),
    )
    row = fetch_first("performance_action_types", {"id": type_id})
    if row is None:
        raise InvalidInputError("نوع تشویق یا تنبیه پیدا نشد")
    return row


def _cash_transaction_type(category: str) -> str:
    if category == REWARD_CATEGORY:
        return TX_TYPE_REWARD
    if category == PENALTY_CATEGORY:
        return TX_TYPE_PENALTY
    raise InvalidInputError("دستهٔ نوع اقدام نامعتبر است")


def _signed_transaction_amount(category: str, amount: Decimal) -> Decimal:
    """پاداش از حساب کم می‌شود؛ جریمه به حساب برمی‌گردد."""
    magnitude = abs(amount)
    if category == REWARD_CATEGORY:
        return -magnitude
    return magnitude


def fetch_performance_action(row_id: int) -> dict:
    """یک اقدام را با شناسه می‌خواند."""
    row = fetch_performance_action_record(row_id)
    if row is None:
        raise PerformanceActionNotFoundError(_not_found_message(row_id))
    return row


def fetch_performance_actions(
    limit: int,
    offset: int,
    user_id=None,
    project_id=None,
) -> list:
    """اقدام‌ها را با فیلتر اختیاری کاربر یا پروژه می‌خواند."""
    if user_id is not None:
        fetch_user(user_id)
    if project_id is not None:
        fetch_project(project_id)
    return fetch_performance_action_records(
        limit,
        offset,
        user_id=user_id,
        project_id=project_id,
    )


def score_totals_for_user(user_id: int) -> dict:
    """جمع امتیاز جدول امتیاز و جمع امتیاز اقدام‌های همان کاربر."""
    fetch_user(user_id)
    return {
        "scores_total": sum_performance_scores_for_user(user_id),
        "actions_total": sum_performance_action_scores_for_user(user_id),
    }


def insert_performance_action(fields: dict, created_by: int) -> int:
    """اقدام را درج می‌کند؛ امتیاز و تراکنش نقدی اثر جانبی همان تراکنش‌اند."""
    subject = fetch_user(fields["user_id"])
    if subject.get("is_active") is False:
        raise InvalidInputError("کاربر غیرفعال نمی‌تواند ارزیابی شود")
    project_id = fields.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
    action_type = _resolve_action_type(fields)
    reason = _require_reason(fields.get("reason"))
    score = fields.get("score")
    amount = fields.get("amount")
    if amount is not None:
        amount = Decimal(str(amount))
    account_id = fields.get("account_id")
    if amount is not None and account_id is None:
        raise InvalidInputError("برای مبلغ نقدی حساب لازم است")
    if account_id is not None and amount is None:
        raise InvalidInputError("حساب بدون مبلغ نقدی مجاز نیست")
    if score == 0:
        raise InvalidInputError("امتیاز صفر مجاز نیست")
    account = None
    if amount is not None:
        account = fetch_financial_account_record(account_id)
        if account is None:
            raise InvalidInputError(f"حساب با شناسه {account_id} پیدا نشد")
        if account.get("is_active") is False:
            raise InvalidInputError("حساب غیرفعال است")
        transaction_type_id = resolve_lookup_id(
            "transaction_types",
            None,
            _cash_transaction_type(action_type["category"]),
        )
    else:
        transaction_type_id = None

    def work(connection):
        transaction_id = None
        if amount is not None:
            transaction_id = insert_cash_transaction_on(
                connection,
                {
                    "account_id": account_id,
                    "project_id": project_id,
                    "user_id": subject["id"],
                    "category_id": None,
                    "transaction_type_id": transaction_type_id,
                    "amount": _signed_transaction_amount(
                        action_type["category"],
                        amount,
                    ),
                    "description": reason,
                },
            )
            if transaction_id is None:
                raise InvalidInputError(f"حساب با شناسه {account_id} پیدا نشد")
        action_id = insert_row_on(
            connection,
            "performance_actions",
            {
                "user_id": subject["id"],
                "project_id": project_id,
                "type_id": action_type["id"],
                "reason": reason,
                "amount": amount,
                "score": score,
                "financial_transaction_id": transaction_id,
                "created_by_user_id": created_by,
            },
        )
        if score is not None:
            insert_row_on(
                connection,
                "performance_scores",
                {
                    "user_id": subject["id"],
                    "project_id": project_id,
                    "score": score,
                    "reason": reason,
                    "source": SCORE_SOURCE,
                    "performance_action_id": action_id,
                },
            )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "PerformanceAction",
            action_id,
            None,
            {
                "user_id": subject["id"],
                "project_id": project_id,
                "type_id": action_type["id"],
                "score": score,
                "amount": str(amount) if amount is not None else None,
                "financial_transaction_id": transaction_id,
            },
        )
        return action_id

    return run_query(work)


insert_performance_action = logged_step("insert")(insert_performance_action)
fetch_performance_action = logged_step("fetch")(fetch_performance_action)
fetch_performance_actions = logged_step("fetch")(fetch_performance_actions)
score_totals_for_user = logged_step("fetch")(score_totals_for_user)
