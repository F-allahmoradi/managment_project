"""کوئری‌های فقط‌خواندنی آمار: SELECT و GROUP BY روی PostgreSQL.

INSERT/UPDATE/DELETE اینجا نیست. محدوده با عضویت فعال پروژه است.
"""

from logging_module import logged_step
from repository.db import fetch_many, fetch_one

from business_logic.loader import (
    cancelled_project_status,
    cancelled_task_status,
    completed_project_status,
    completed_task_status,
)

PROJECT_PROGRESS_COLUMNS = (
    "project_id",
    "project_name",
    "project_status",
    "end_date",
    "days_remaining",
    "task_count",
    "completed_count",
    "cancelled_count",
    "open_count",
    "overdue_count",
)

OVERDUE_TASK_COLUMNS = (
    "id",
    "project_id",
    "project_name",
    "title",
    "due_date",
    "status",
    "assigned_to_user_id",
    "assignee_name",
    "days_overdue",
)

TASK_STATUS_COLUMNS = ("status", "count")

MEMBER_WORKLOAD_COLUMNS = (
    "user_id",
    "first_name",
    "last_name",
    "open_tasks",
    "overdue_tasks",
    "completed_tasks",
)

FOLLOW_UP_COUNT_COLUMNS = (
    "task_id",
    "project_id",
    "title",
    "follow_up_count",
)

MESSAGE_TYPE_COLUMNS = ("message_type", "count")

MEMBER_SCORE_COLUMNS = (
    "user_id",
    "first_name",
    "last_name",
    "total_score",
    "reward_count",
    "penalty_count",
)

PERFORMANCE_DASHBOARD_COLUMNS = (
    "reward_count",
    "penalty_count",
    "total_score",
    "total_amount",
)

PROJECT_COST_COLUMNS = ("project_id", "income", "expense", "net")

TRANSACTION_SUMMARY_COLUMNS = ("income", "expense", "net", "transaction_count")

DELIVERY_STAT_COLUMNS = ("status", "count")

AT_RISK_PROJECT_COLUMNS = (
    "project_id",
    "project_name",
    "project_status",
    "end_date",
    "days_remaining",
    "task_count",
    "completed_count",
    "overdue_count",
)


def _closed_task_names() -> tuple[str, str]:
    return completed_task_status(), cancelled_task_status()


def fetch_project_task_counts(project_id: int):
    """شمارش وظایف یک پروژه را با وضعیت تکمیل‌شده برمی‌گرداند یا None."""
    completed, cancelled = _closed_task_names()
    return fetch_one(
        """
        SELECT p.id AS project_id,
               p.name AS project_name,
               ps.name AS project_status,
               p.end_date,
               CASE
                   WHEN p.end_date IS NULL THEN NULL
                   ELSE (p.end_date - CURRENT_DATE)
               END AS days_remaining,
               COUNT(t.id) AS task_count,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS completed_count,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS cancelled_count,
               COUNT(t.id) FILTER (
                   WHERE ts.name IS NOT NULL
                     AND ts.name NOT IN (%s, %s)
               ) AS open_count,
               COUNT(t.id) FILTER (
                   WHERE t.due_date < CURRENT_DATE
                     AND ts.name NOT IN (%s, %s)
               ) AS overdue_count
        FROM projects p
        JOIN project_statuses ps ON ps.id = p.project_status_id
        LEFT JOIN tasks t ON t.project_id = p.id
        LEFT JOIN task_statuses ts ON ts.id = t.status_id
        WHERE p.id = %s
        GROUP BY p.id, p.name, ps.name, p.end_date
        """,
        [
            completed,
            cancelled,
            completed,
            cancelled,
            completed,
            cancelled,
            project_id,
        ],
        PROJECT_PROGRESS_COLUMNS,
    )


def fetch_overdue_task_records(
    actor_id: int,
    project_id,
    limit: int,
    offset: int,
) -> list:
    """وظایف باز گذشته از مهلت را در پروژه‌های عضو فعال می‌خواند."""
    completed, cancelled = _closed_task_names()
    clauses = [
        "pm.user_id = %s",
        "pm.is_active = true",
        "t.due_date < CURRENT_DATE",
        "ts.name NOT IN (%s, %s)",
    ]
    params = [actor_id, completed, cancelled]
    if project_id is not None:
        clauses.append("t.project_id = %s")
        params.append(project_id)
    params.extend([limit, offset])
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT t.id, t.project_id, p.name AS project_name, t.title,
               t.due_date, ts.name AS status, t.assigned_to_user_id,
               NULLIF(btrim(concat_ws(' ', u.first_name, u.last_name)), '')
                   AS assignee_name,
               (CURRENT_DATE - t.due_date) AS days_overdue
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        JOIN task_statuses ts ON ts.id = t.status_id
        JOIN project_members pm ON pm.project_id = t.project_id
        LEFT JOIN users u ON u.id = t.assigned_to_user_id
        WHERE {where}
        ORDER BY t.due_date ASC, t.id ASC
        LIMIT %s OFFSET %s
        """,
        params,
        OVERDUE_TASK_COLUMNS,
    )


def fetch_task_status_breakdown_records(actor_id: int, project_id) -> list:
    """توزیع وضعیت وظایف را در محدودهٔ عضو فعال برمی‌گرداند."""
    clauses = ["pm.user_id = %s", "pm.is_active = true"]
    params = [actor_id]
    if project_id is not None:
        clauses.append("t.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT ts.name AS status, COUNT(t.id) AS count
        FROM tasks t
        JOIN task_statuses ts ON ts.id = t.status_id
        JOIN project_members pm ON pm.project_id = t.project_id
        WHERE {where}
        GROUP BY ts.name
        ORDER BY COUNT(t.id) DESC, ts.name ASC
        """,
        params,
        TASK_STATUS_COLUMNS,
    )


def fetch_task_completion_counts(actor_id: int, project_id):
    """شمار تکمیل و کل وظایف محدودهٔ عضو فعال را برمی‌گرداند."""
    completed, cancelled = _closed_task_names()
    clauses = ["pm.user_id = %s", "pm.is_active = true"]
    params = [completed, cancelled, actor_id]
    if project_id is not None:
        clauses.append("t.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    return fetch_one(
        f"""
        SELECT COUNT(t.id) AS task_count,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS completed_count,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS cancelled_count
        FROM tasks t
        JOIN task_statuses ts ON ts.id = t.status_id
        JOIN project_members pm ON pm.project_id = t.project_id
        WHERE {where}
        """,
        params,
        ("task_count", "completed_count", "cancelled_count"),
    )


def fetch_at_risk_project_records(actor_id: int, limit: int, offset: int) -> list:
    """پروژه‌های عضو فعال با وظیفهٔ عقب‌افتاده یا مهلت گذشته را می‌خواند."""
    completed, cancelled = _closed_task_names()
    project_done = completed_project_status()
    project_cancelled = cancelled_project_status()
    return fetch_many(
        """
        SELECT p.id AS project_id,
               p.name AS project_name,
               ps.name AS project_status,
               p.end_date,
               CASE
                   WHEN p.end_date IS NULL THEN NULL
                   ELSE (p.end_date - CURRENT_DATE)
               END AS days_remaining,
               COUNT(t.id) AS task_count,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS completed_count,
               COUNT(t.id) FILTER (
                   WHERE t.due_date < CURRENT_DATE
                     AND ts.name NOT IN (%s, %s)
               ) AS overdue_count
        FROM projects p
        JOIN project_statuses ps ON ps.id = p.project_status_id
        JOIN project_members pm
          ON pm.project_id = p.id
         AND pm.user_id = %s
         AND pm.is_active = true
        LEFT JOIN tasks t ON t.project_id = p.id
        LEFT JOIN task_statuses ts ON ts.id = t.status_id
        GROUP BY p.id, p.name, ps.name, p.end_date
        HAVING COUNT(t.id) FILTER (
                   WHERE t.due_date < CURRENT_DATE
                     AND ts.name NOT IN (%s, %s)
               ) > 0
            OR (
                p.end_date < CURRENT_DATE
                AND ps.name NOT IN (%s, %s)
            )
        ORDER BY overdue_count DESC, p.id ASC
        LIMIT %s OFFSET %s
        """,
        [
            completed,
            completed,
            cancelled,
            actor_id,
            completed,
            cancelled,
            project_done,
            project_cancelled,
            limit,
            offset,
        ],
        AT_RISK_PROJECT_COLUMNS,
    )


def fetch_member_workload_records(actor_id: int, project_id, user_id) -> list:
    """بار کاری اعضای پروژه‌های قابل‌مشاهده را برمی‌گرداند."""
    completed, cancelled = _closed_task_names()
    clauses = ["viewer.user_id = %s", "viewer.is_active = true", "pm.is_active = true"]
    params = [completed, cancelled, completed, cancelled, completed, actor_id]
    if project_id is not None:
        clauses.append("pm.project_id = %s")
        params.append(project_id)
    if user_id is not None:
        clauses.append("pm.user_id = %s")
        params.append(user_id)
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT u.id AS user_id, u.first_name, u.last_name,
               COUNT(t.id) FILTER (
                   WHERE ts.name NOT IN (%s, %s)
               ) AS open_tasks,
               COUNT(t.id) FILTER (
                   WHERE t.due_date < CURRENT_DATE
                     AND ts.name NOT IN (%s, %s)
               ) AS overdue_tasks,
               COUNT(t.id) FILTER (WHERE ts.name = %s) AS completed_tasks
        FROM project_members pm
        JOIN project_members viewer ON viewer.project_id = pm.project_id
        JOIN users u ON u.id = pm.user_id
        LEFT JOIN tasks t
          ON t.assigned_to_user_id = u.id
         AND t.project_id = pm.project_id
        LEFT JOIN task_statuses ts ON ts.id = t.status_id
        WHERE {where}
        GROUP BY u.id, u.first_name, u.last_name
        ORDER BY overdue_tasks DESC, open_tasks DESC, u.id ASC
        """,
        params,
        MEMBER_WORKLOAD_COLUMNS,
    )


def fetch_follow_up_count_records(
    actor_id: int,
    project_id,
    min_count: int,
    limit: int,
    offset: int,
) -> list:
    """تعداد پیگیری هر وظیفه را در محدودهٔ عضو فعال می‌خواند."""
    clauses = ["pm.user_id = %s", "pm.is_active = true"]
    params = [actor_id]
    if project_id is not None:
        clauses.append("t.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    params.extend([min_count, limit, offset])
    return fetch_many(
        f"""
        SELECT t.id AS task_id, t.project_id, t.title,
               COUNT(fu.id) AS follow_up_count
        FROM tasks t
        JOIN project_members pm ON pm.project_id = t.project_id
        LEFT JOIN task_follow_ups fu ON fu.task_id = t.id
        WHERE {where}
        GROUP BY t.id, t.project_id, t.title
        HAVING COUNT(fu.id) >= %s
        ORDER BY COUNT(fu.id) DESC, t.id ASC
        LIMIT %s OFFSET %s
        """,
        params,
        FOLLOW_UP_COUNT_COLUMNS,
    )


def fetch_message_type_count_records(actor_id: int, project_id) -> list:
    """شمار پیام‌ها را بر اساس نوع در گفتگوی پروژه‌های عضو می‌خواند."""
    clauses = [
        "pm.user_id = %s",
        "pm.is_active = true",
        "c.project_id IS NOT NULL",
    ]
    params = [actor_id]
    if project_id is not None:
        clauses.append("c.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT COALESCE(d.name, 'بدون تحلیل') AS message_type, COUNT(m.id) AS count
        FROM messages m
        JOIN chats c ON c.id = m.chat_id
        JOIN project_members pm ON pm.project_id = c.project_id
        LEFT JOIN LATERAL (
            SELECT dt.name
            FROM text_analyses ta
            JOIN analysis_source_types st ON st.id = ta.source_type_id
            JOIN text_analysis_discourses tad
                ON tad.analysis_id = ta.id AND tad.is_primary
            JOIN discourse_types dt ON dt.id = tad.discourse_type_id
            WHERE st.code = 'message' AND ta.source_id = m.id
            ORDER BY ta.created_at DESC
            LIMIT 1
        ) d ON true
        WHERE {where}
        GROUP BY COALESCE(d.name, 'بدون تحلیل')
        ORDER BY COUNT(m.id) DESC, COALESCE(d.name, 'بدون تحلیل') ASC
        """,
        params,
        MESSAGE_TYPE_COLUMNS,
    )


def fetch_member_score_records(actor_id: int, project_id, user_id) -> list:
    """جمع امتیاز و شمار تشویق/تنبیه اعضا را در محدودهٔ مجاز می‌خواند."""
    score_scope = """
        AND ps.project_id IN (
            SELECT v.project_id FROM project_members v
            WHERE v.user_id = %s AND v.is_active = true
        )
    """
    action_scope = """
        AND pa.project_id IN (
            SELECT v.project_id FROM project_members v
            WHERE v.user_id = %s AND v.is_active = true
        )
    """
    clauses = ["viewer.user_id = %s", "viewer.is_active = true", "pm.is_active = true"]
    params = [actor_id, actor_id, actor_id, actor_id]
    if project_id is not None:
        score_scope = "AND ps.project_id = %s"
        action_scope = "AND pa.project_id = %s"
        params = [project_id, project_id, project_id, actor_id]
        clauses.append("pm.project_id = %s")
        params.append(project_id)
    if user_id is not None:
        clauses.append("pm.user_id = %s")
        params.append(user_id)
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT u.id AS user_id, u.first_name, u.last_name,
               COALESCE((
                   SELECT SUM(ps.score)
                   FROM performance_scores ps
                   WHERE ps.user_id = u.id
                     {score_scope}
               ), 0) AS total_score,
               COALESCE((
                   SELECT COUNT(*)
                   FROM performance_actions pa
                   JOIN performance_action_types pat ON pat.id = pa.type_id
                   WHERE pa.user_id = u.id
                     AND pat.category = 'REWARD'
                     {action_scope}
               ), 0) AS reward_count,
               COALESCE((
                   SELECT COUNT(*)
                   FROM performance_actions pa
                   JOIN performance_action_types pat ON pat.id = pa.type_id
                   WHERE pa.user_id = u.id
                     AND pat.category = 'PENALTY'
                     {action_scope}
               ), 0) AS penalty_count
        FROM project_members pm
        JOIN project_members viewer ON viewer.project_id = pm.project_id
        JOIN users u ON u.id = pm.user_id
        WHERE {where}
        GROUP BY u.id, u.first_name, u.last_name
        ORDER BY total_score DESC, u.id ASC
        """,
        params,
        MEMBER_SCORE_COLUMNS,
    )


def fetch_performance_dashboard_record(actor_id: int, project_id):
    """خلاصهٔ تشویق و تنبیه را در پروژه‌های عضو فعال برمی‌گرداند."""
    clauses = [
        "pm.user_id = %s",
        "pm.is_active = true",
        "pa.project_id IS NOT NULL",
    ]
    params = [actor_id]
    if project_id is not None:
        clauses.append("pa.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    return fetch_one(
        f"""
        SELECT COUNT(*) FILTER (WHERE pat.category = 'REWARD') AS reward_count,
               COUNT(*) FILTER (WHERE pat.category = 'PENALTY') AS penalty_count,
               COALESCE(SUM(pa.score), 0) AS total_score,
               COALESCE(SUM(pa.amount), 0) AS total_amount
        FROM performance_actions pa
        JOIN performance_action_types pat ON pat.id = pa.type_id
        JOIN project_members pm ON pm.project_id = pa.project_id
        WHERE {where}
        """,
        params,
        PERFORMANCE_DASHBOARD_COLUMNS,
    )


def fetch_project_cost_record(project_id: int):
    """جمع دریافت و پرداخت یک پروژه را برمی‌گرداند."""
    return fetch_one(
        """
        SELECT %s AS project_id,
               COALESCE(SUM(amount) FILTER (WHERE amount > 0), 0) AS income,
               COALESCE(SUM(amount) FILTER (WHERE amount < 0), 0) AS expense,
               COALESCE(SUM(amount), 0) AS net
        FROM financial_transactions
        WHERE project_id = %s
        """,
        [project_id, project_id],
        PROJECT_COST_COLUMNS,
    )


def fetch_transaction_summary_record(actor_id: int, project_id, account_id):
    """جمع تراکنش‌های قابل‌مشاهده را با فیلتر اختیاری برمی‌گرداند."""
    clauses = []
    params = []
    if project_id is not None:
        clauses.append("tx.project_id = %s")
        params.append(project_id)
    else:
        clauses.append(
            """
            (
                tx.project_id IN (
                    SELECT pm.project_id
                    FROM project_members pm
                    WHERE pm.user_id = %s AND pm.is_active = true
                )
                OR tx.project_id IS NULL
            )
            """
        )
        params.append(actor_id)
    if account_id is not None:
        clauses.append("tx.account_id = %s")
        params.append(account_id)
    where = " AND ".join(clauses)
    return fetch_one(
        f"""
        SELECT COALESCE(SUM(amount) FILTER (WHERE amount > 0), 0) AS income,
               COALESCE(SUM(amount) FILTER (WHERE amount < 0), 0) AS expense,
               COALESCE(SUM(amount), 0) AS net,
               COUNT(*) AS transaction_count
        FROM financial_transactions tx
        WHERE {where}
        """,
        params,
        TRANSACTION_SUMMARY_COLUMNS,
    )


def fetch_delivery_stat_records(actor_id: int, project_id) -> list:
    """شمار ارسال موفق/ناموفق یادآوری را در محدودهٔ عضو فعال می‌خواند."""
    clauses = ["pm.user_id = %s", "pm.is_active = true", "r.project_id IS NOT NULL"]
    params = [actor_id]
    if project_id is not None:
        clauses.append("r.project_id = %s")
        params.append(project_id)
    where = " AND ".join(clauses)
    return fetch_many(
        f"""
        SELECT el.status, COUNT(el.id) AS count
        FROM execution_logs el
        JOIN reminders r ON r.id = el.reminder_id
        JOIN project_members pm ON pm.project_id = r.project_id
        WHERE {where}
        GROUP BY el.status
        ORDER BY COUNT(el.id) DESC, el.status ASC
        """,
        params,
        DELIVERY_STAT_COLUMNS,
    )


fetch_project_task_counts = logged_step("fetch")(fetch_project_task_counts)
fetch_overdue_task_records = logged_step("fetch")(fetch_overdue_task_records)
fetch_task_status_breakdown_records = logged_step("fetch")(
    fetch_task_status_breakdown_records
)
fetch_task_completion_counts = logged_step("fetch")(fetch_task_completion_counts)
fetch_at_risk_project_records = logged_step("fetch")(fetch_at_risk_project_records)
fetch_member_workload_records = logged_step("fetch")(fetch_member_workload_records)
fetch_follow_up_count_records = logged_step("fetch")(fetch_follow_up_count_records)
fetch_message_type_count_records = logged_step("fetch")(
    fetch_message_type_count_records
)
fetch_member_score_records = logged_step("fetch")(fetch_member_score_records)
fetch_performance_dashboard_record = logged_step("fetch")(
    fetch_performance_dashboard_record
)
fetch_project_cost_record = logged_step("fetch")(fetch_project_cost_record)
fetch_transaction_summary_record = logged_step("fetch")(
    fetch_transaction_summary_record
)
fetch_delivery_stat_records = logged_step("fetch")(fetch_delivery_stat_records)
