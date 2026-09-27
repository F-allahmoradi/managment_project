"""ترکیب کوئری و درصد برای پاسخ ابزارهای آمار.

مجوز و عضویت در ابزار MCP است؛ اینجا فقط عدد ساخته می‌شود.
"""

from errors.crud import ProjectNotFoundError
from logging_module import logged_step

from business_logic.calculator import (
    completion_rate,
    health_label,
    progress_percent,
)
from business_logic.loader import (
    cancelled_project_status,
    completed_project_status,
    repeated_follow_up_threshold,
)
from business_logic.repository import (
    fetch_at_risk_project_records,
    fetch_delivery_stat_records,
    fetch_follow_up_count_records,
    fetch_member_score_records,
    fetch_member_workload_records,
    fetch_message_type_count_records,
    fetch_overdue_task_records,
    fetch_performance_dashboard_record,
    fetch_project_cost_record,
    fetch_project_task_counts,
    fetch_task_completion_counts,
    fetch_task_status_breakdown_records,
    fetch_transaction_summary_record,
)


def _not_found(project_id: int) -> str:
    return f"پروژه با شناسه {project_id} پیدا نشد"


def _with_progress(row: dict) -> dict:
    payload = dict(row)
    payload["progress_percent"] = progress_percent(
        int(row.get("completed_count") or 0),
        int(row.get("task_count") or 0),
    )
    return payload


def _with_health(row: dict) -> dict:
    payload = _with_progress(row)
    payload["health"] = health_label(
        int(row.get("overdue_count") or 0),
        row.get("days_remaining"),
        str(row.get("project_status") or ""),
        completed_project_status(),
        cancelled_project_status(),
    )
    return payload


def project_progress(project_id: int) -> dict:
    """درصد پیشرفت یک پروژه را از شمار وظایف می‌سازد."""
    row = fetch_project_task_counts(project_id)
    if row is None:
        raise ProjectNotFoundError(_not_found(project_id))
    return _with_progress(row)


def project_health(project_id: int) -> dict:
    """وضعیت کلی پروژه را با درصد و برچسب سلامت برمی‌گرداند."""
    row = fetch_project_task_counts(project_id)
    if row is None:
        raise ProjectNotFoundError(_not_found(project_id))
    return _with_health(row)


def at_risk_projects(actor_id: int, limit: int, offset: int) -> list:
    """پروژه‌های در معرض تأخیر کاربر جاری را فهرست می‌کند."""
    rows = fetch_at_risk_project_records(actor_id, limit, offset)
    return [_with_health(row) for row in rows]


def overdue_tasks(actor_id: int, project_id, limit: int, offset: int) -> list:
    """وظایف گذشته از مهلت را در محدودهٔ عضو فعال برمی‌گرداند."""
    return fetch_overdue_task_records(actor_id, project_id, limit, offset)


def task_status_breakdown(actor_id: int, project_id) -> list:
    """توزیع وضعیت وظایف را برمی‌گرداند."""
    return fetch_task_status_breakdown_records(actor_id, project_id)


def task_completion_stats(actor_id: int, project_id) -> dict:
    """نرخ تکمیل وظایف محدوده را برمی‌گرداند."""
    row = fetch_task_completion_counts(actor_id, project_id) or {
        "task_count": 0,
        "completed_count": 0,
        "cancelled_count": 0,
    }
    task_count = int(row.get("task_count") or 0)
    completed_count = int(row.get("completed_count") or 0)
    cancelled_count = int(row.get("cancelled_count") or 0)
    open_count = task_count - completed_count - cancelled_count
    return {
        "task_count": task_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "open_count": open_count,
        "completion_rate": completion_rate(completed_count, task_count),
    }


def member_workload(actor_id: int, project_id, user_id) -> list:
    """بار کاری اعضا را برمی‌گرداند."""
    return fetch_member_workload_records(actor_id, project_id, user_id)


def members_needing_attention(actor_id: int, project_id) -> list:
    """اعضایی را برمی‌گرداند که وظیفهٔ عقب‌افتاده دارند."""
    rows = fetch_member_workload_records(actor_id, project_id, None)
    return [row for row in rows if int(row.get("overdue_tasks") or 0) > 0]


def follow_up_counts(
    actor_id: int,
    project_id,
    min_count: int,
    limit: int,
    offset: int,
) -> list:
    """شمار پیگیری وظایف را برمی‌گرداند."""
    return fetch_follow_up_count_records(
        actor_id,
        project_id,
        min_count,
        limit,
        offset,
    )


def repeated_follow_ups(
    actor_id: int,
    project_id,
    min_count,
    limit: int,
    offset: int,
) -> list:
    """وظایفی را برمی‌گرداند که بیش از آستانه پیگیری شده‌اند."""
    threshold = (
        repeated_follow_up_threshold() if min_count is None else min_count
    )
    if threshold < 1:
        threshold = repeated_follow_up_threshold()
    return fetch_follow_up_count_records(
        actor_id,
        project_id,
        threshold,
        limit,
        offset,
    )


def message_type_counts(actor_id: int, project_id) -> list:
    """شمار پیام‌ها بر اساس نوع را برمی‌گرداند."""
    return fetch_message_type_count_records(actor_id, project_id)


def member_scores(actor_id: int, project_id, user_id) -> list:
    """امتیاز اعضا را برمی‌گرداند."""
    return fetch_member_score_records(actor_id, project_id, user_id)


def performance_dashboard(actor_id: int, project_id) -> dict:
    """خلاصهٔ تشویق و تنبیه محدوده را برمی‌گرداند."""
    row = fetch_performance_dashboard_record(actor_id, project_id)
    if row is None:
        return {
            "reward_count": 0,
            "penalty_count": 0,
            "total_score": 0,
            "total_amount": 0,
        }
    return row


def project_costs(project_id: int) -> dict:
    """جمع هزینه و دریافت یک پروژه را برمی‌گرداند."""
    row = fetch_project_cost_record(project_id)
    if row is None:
        return {
            "project_id": project_id,
            "income": 0,
            "expense": 0,
            "net": 0,
        }
    return row


def transaction_summary(actor_id: int, project_id, account_id) -> dict:
    """جمع تراکنش‌های قابل‌مشاهده را برمی‌گرداند."""
    row = fetch_transaction_summary_record(actor_id, project_id, account_id)
    if row is None:
        return {
            "income": 0,
            "expense": 0,
            "net": 0,
            "transaction_count": 0,
        }
    return row


def delivery_stats(actor_id: int, project_id) -> list:
    """شمار ارسال موفق و ناموفق یادآوری را برمی‌گرداند."""
    return fetch_delivery_stat_records(actor_id, project_id)


project_progress = logged_step("analyze")(project_progress)
project_health = logged_step("analyze")(project_health)
at_risk_projects = logged_step("analyze")(at_risk_projects)
overdue_tasks = logged_step("analyze")(overdue_tasks)
task_status_breakdown = logged_step("analyze")(task_status_breakdown)
task_completion_stats = logged_step("analyze")(task_completion_stats)
member_workload = logged_step("analyze")(member_workload)
members_needing_attention = logged_step("analyze")(members_needing_attention)
follow_up_counts = logged_step("analyze")(follow_up_counts)
repeated_follow_ups = logged_step("analyze")(repeated_follow_ups)
message_type_counts = logged_step("analyze")(message_type_counts)
member_scores = logged_step("analyze")(member_scores)
performance_dashboard = logged_step("analyze")(performance_dashboard)
project_costs = logged_step("analyze")(project_costs)
transaction_summary = logged_step("analyze")(transaction_summary)
delivery_stats = logged_step("analyze")(delivery_stats)
