"""کوئری‌های JOIN که از INSERT/UPDATE ساده فراترند.

هر SELECT با JOIN فقط یک‌بار این‌جا است؛ سرویس دامنه تکرارش نمی‌کند.
"""

from errors.crud import InvalidInputError
from repository.db import fetch_many, fetch_one
from repository.soft_delete import CANCELLED_STATUS_NAME

PROJECT_COLUMNS = (
    "id",
    "name",
    "description",
    "project_type_id",
    "project_type_name",
    "project_status_id",
    "project_status_name",
    "start_date",
    "end_date",
    "created_by",
    "created_at",
)
_PROJECT_SELECT = """
SELECT p.id, p.name, p.description,
       p.project_type_id, pt.name AS project_type_name,
       p.project_status_id, ps.name AS project_status_name,
       p.start_date, p.end_date, p.created_by, p.created_at
FROM projects p
JOIN project_types pt ON pt.id = p.project_type_id
JOIN project_statuses ps ON ps.id = p.project_status_id
"""

MEMBER_COLUMNS = (
    "id",
    "project_id",
    "user_id",
    "username",
    "project_role_id",
    "project_role_name",
    "joined_at",
    "is_active",
)
_MEMBER_SELECT = """
SELECT pm.id, pm.project_id, pm.user_id, u.username,
       pm.project_role_id, pr.name AS project_role_name,
       pm.joined_at, pm.is_active
FROM project_members pm
JOIN users u ON u.id = pm.user_id
JOIN project_roles pr ON pr.id = pm.project_role_id
"""

USER_ROLE_COLUMNS = (
    "id",
    "user_id",
    "role_id",
    "username",
    "role_name",
    "is_system_role",
)
_USER_ROLE_SELECT = """
SELECT ur.id, ur.user_id, ur.role_id,
       u.username, r.name AS role_name, r.is_system_role
FROM user_roles ur
JOIN users u ON u.id = ur.user_id
JOIN roles r ON r.id = ur.role_id
"""

ROLE_PERMISSION_COLUMNS = (
    "id",
    "role_id",
    "permission_id",
    "role_name",
    "permission_name",
    "resource",
    "action",
)
_ROLE_PERMISSION_SELECT = """
SELECT rp.id, rp.role_id, rp.permission_id,
       r.name AS role_name, p.name AS permission_name,
       p.resource, p.action
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
"""

TASK_COLUMNS = (
    "id",
    "project_id",
    "project_name",
    "title",
    "description",
    "assigned_to_user_id",
    "assigned_to_username",
    "created_by_user_id",
    "status_id",
    "status_name",
    "priority_id",
    "priority_name",
    "importance_id",
    "importance_name",
    "importance_percent",
    "start_date",
    "due_date",
    "completed_at",
    "created_at",
)
_TASK_SELECT = """
SELECT t.id, t.project_id, p.name AS project_name,
       t.title, t.description,
       t.assigned_to_user_id, assignee.username AS assigned_to_username,
       t.created_by_user_id,
       t.status_id, ts.name AS status_name,
       t.priority_id, tp.name AS priority_name,
       t.importance_id, ti.name AS importance_name,
       t.importance_percent, t.start_date, t.due_date,
       t.completed_at, t.created_at
FROM tasks t
JOIN projects p ON p.id = t.project_id
JOIN task_statuses ts ON ts.id = t.status_id
JOIN task_priorities tp ON tp.id = t.priority_id
JOIN task_importances ti ON ti.id = t.importance_id
LEFT JOIN users assignee ON assignee.id = t.assigned_to_user_id
"""

FOLLOW_UP_COLUMNS = (
    "id",
    "task_id",
    "followed_by_user_id",
    "followed_by_username",
    "follow_up_type_id",
    "follow_up_type_name",
    "status_id",
    "status_name",
    "note",
    "follow_up_date",
    "next_follow_up_date",
    "created_at",
)
_FOLLOW_UP_SELECT = """
SELECT f.id, f.task_id,
       f.followed_by_user_id, u.username AS followed_by_username,
       f.follow_up_type_id, ft.name AS follow_up_type_name,
       f.status_id, fs.name AS status_name,
       f.note, f.follow_up_date, f.next_follow_up_date, f.created_at
FROM task_follow_ups f
JOIN users u ON u.id = f.followed_by_user_id
JOIN follow_up_types ft ON ft.id = f.follow_up_type_id
JOIN task_follow_up_statuses fs ON fs.id = f.status_id
"""

def fetch_project_record(project_id: int):
    """یک پروژه را با نام نوع و وضعیت می‌خواند."""
    return fetch_one(
        f"{_PROJECT_SELECT} WHERE p.id = %s",
        [project_id],
        PROJECT_COLUMNS,
    )


def fetch_projects_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    unrestricted: bool = False,
) -> list:
    """پروژه‌های قابل‌مشاهده: همه برای مدیر کل، وگرنه عضویت فعال."""
    if unrestricted:
        return fetch_many(
            f"""
            {_PROJECT_SELECT}
            WHERE ps.name <> %s
            ORDER BY p.id DESC
            LIMIT %s OFFSET %s
            """,
            [CANCELLED_STATUS_NAME, limit, offset],
            PROJECT_COLUMNS,
        )
    return fetch_many(
        f"""
        {_PROJECT_SELECT}
        JOIN project_members pm ON pm.project_id = p.id
        WHERE pm.user_id = %s AND pm.is_active = true
          AND ps.name <> %s
        ORDER BY p.id DESC
        LIMIT %s OFFSET %s
        """,
        [user_id, CANCELLED_STATUS_NAME, limit, offset],
        PROJECT_COLUMNS,
    )


def fetch_active_membership_record(project_id: int, user_id: int):
    """عضویت فعال کاربر در پروژه را برمی‌گرداند یا None."""
    return fetch_one(
        """
        SELECT id, project_id, user_id, project_role_id, is_active
        FROM project_members
        WHERE project_id = %s AND user_id = %s AND is_active = true
        """,
        [project_id, user_id],
        ("id", "project_id", "user_id", "project_role_id", "is_active"),
    )


def fetch_member_record(row_id: int):
    """یک عضویت را با نام کاربر و نقش داخل پروژه می‌خواند."""
    return fetch_one(
        f"{_MEMBER_SELECT} WHERE pm.id = %s",
        [row_id],
        MEMBER_COLUMNS,
    )


def fetch_members_for_project_records(project_id: int, limit: int, offset: int) -> list:
    """اعضای یک پروژه را با صفحه‌بندی می‌خواند."""
    return fetch_many(
        f"""
        {_MEMBER_SELECT}
        WHERE pm.project_id = %s
        ORDER BY pm.id ASC
        LIMIT %s OFFSET %s
        """,
        [project_id, limit, offset],
        MEMBER_COLUMNS,
    )


def fetch_user_role_records(user_id, limit: int, offset: int) -> list:
    """اتصال‌های فعال کاربر-نقش را با نام نقش می‌خواند."""
    params = []
    clauses = ["ur.is_active = true", "r.is_active = true"]
    if user_id is not None:
        clauses.append("ur.user_id = %s")
        params.append(user_id)
    params.extend([limit, offset])
    return fetch_many(
        f"""
        {_USER_ROLE_SELECT}
        WHERE {" AND ".join(clauses)}
        ORDER BY ur.id ASC
        LIMIT %s OFFSET %s
        """,
        params,
        USER_ROLE_COLUMNS,
    )


def fetch_role_permission_records(role_id, limit: int, offset: int) -> list:
    """اتصال‌های فعال نقش-مجوز را با جزئیات مجوز می‌خواند."""
    params = []
    clauses = ["rp.is_active = true", "r.is_active = true"]
    if role_id is not None:
        clauses.append("rp.role_id = %s")
        params.append(role_id)
    params.extend([limit, offset])
    return fetch_many(
        f"""
        {_ROLE_PERMISSION_SELECT}
        WHERE {" AND ".join(clauses)}
        ORDER BY rp.id ASC
        LIMIT %s OFFSET %s
        """,
        params,
        ROLE_PERMISSION_COLUMNS,
    )


TASK_ITEM_COLUMNS = (
    "id",
    "task_id",
    "parent_item_id",
    "title",
    "description",
    "sort_order",
    "start_date",
    "end_date",
    "is_completed",
    "completed_at",
    "completed_by_user_id",
    "completed_by_username",
    "created_by_user_id",
    "created_by_username",
    "created_at",
    "updated_at",
)
_TASK_ITEM_SELECT = """
SELECT i.id, i.task_id, i.parent_item_id, i.title, i.description,
       i.sort_order, i.start_date, i.end_date,
       i.is_completed, i.completed_at, i.completed_by_user_id,
       completer.username AS completed_by_username,
       i.created_by_user_id, creator.username AS created_by_username,
       i.created_at, i.updated_at
FROM task_items i
JOIN users creator ON creator.id = i.created_by_user_id
LEFT JOIN users completer ON completer.id = i.completed_by_user_id
"""


def fetch_task_record(task_id: int):
    """یک وظیفه را با نام پروژه و lookupها می‌خواند."""
    return fetch_one(
        f"{_TASK_SELECT} WHERE t.id = %s",
        [task_id],
        TASK_COLUMNS,
    )


def fetch_tasks_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
    scope: str = "member",
) -> list:
    """وظایف را با محدودهٔ مدیر کل، مدیر سازمان، یا مسئول وظیفه می‌خواند."""
    sql = f"{_TASK_SELECT}"
    params = []
    if scope == "all":
        sql += " WHERE ts.name <> %s"
        params.append(CANCELLED_STATUS_NAME)
    else:
        sql += """
        JOIN project_members pm ON pm.project_id = t.project_id
        WHERE pm.user_id = %s AND pm.is_active = true
          AND ts.name <> %s
        """
        params.extend([user_id, CANCELLED_STATUS_NAME])
        if scope == "assigned":
            sql += " AND t.assigned_to_user_id = %s"
            params.append(user_id)
    if project_id is not None:
        sql += " AND t.project_id = %s"
        params.append(project_id)
    sql += " ORDER BY t.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, TASK_COLUMNS)


def fetch_task_item_record(item_id: int):
    """یک زیرکار فعال را با نام سازنده و تکمیل‌کننده می‌خواند."""
    return fetch_one(
        f"{_TASK_ITEM_SELECT} WHERE i.id = %s AND i.is_active = true",
        [item_id],
        TASK_ITEM_COLUMNS,
    )


def fetch_task_items_for_task_records(task_id: int) -> list:
    """زیرکارهای یک وظیفه را به ترتیب والد و sort_order می‌خواند."""
    return fetch_many(
        f"""
        {_TASK_ITEM_SELECT}
        WHERE i.task_id = %s AND i.is_active = true
        ORDER BY i.parent_item_id NULLS FIRST, i.sort_order ASC, i.id ASC
        """,
        [task_id],
        TASK_ITEM_COLUMNS,
    )


def fetch_task_item_project_id_record(item_id: int):
    """شناسه پروژهٔ وظیفهٔ یک زیرکار را می‌خواند."""
    return fetch_one(
        """
        SELECT t.project_id
        FROM task_items i
        JOIN tasks t ON t.id = i.task_id
        WHERE i.id = %s
        """,
        [item_id],
        ("project_id",),
    )


def fetch_next_task_item_sort_order(task_id: int, parent_item_id) -> int:
    """بعدیِ sort_order را میان خواهرهای همان سطح برمی‌گرداند."""
    row = fetch_one(
        """
        SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order
        FROM task_items
        WHERE task_id = %s
          AND parent_item_id IS NOT DISTINCT FROM %s
        """,
        [task_id, parent_item_id],
        ("next_order",),
    )
    if row is None:
        return 0
    return int(row["next_order"])


def fetch_follow_up_record(follow_up_id: int):
    """یک پیگیری را با نام نوع و نتیجه می‌خواند."""
    return fetch_one(
        f"{_FOLLOW_UP_SELECT} WHERE f.id = %s",
        [follow_up_id],
        FOLLOW_UP_COLUMNS,
    )


def fetch_follow_ups_for_task_records(task_id: int, limit: int, offset: int) -> list:
    """پیگیری‌های یک وظیفه را با صفحه‌بندی می‌خواند."""
    return fetch_many(
        f"""
        {_FOLLOW_UP_SELECT}
        WHERE f.task_id = %s
        ORDER BY f.follow_up_date DESC, f.id DESC
        LIMIT %s OFFSET %s
        """,
        [task_id, limit, offset],
        FOLLOW_UP_COLUMNS,
    )


def fetch_follow_up_project_id_record(follow_up_id: int):
    """شناسه پروژهٔ وظیفهٔ یک پیگیری را می‌خواند."""
    return fetch_one(
        """
        SELECT t.project_id
        FROM task_follow_ups f
        JOIN tasks t ON t.id = f.task_id
        WHERE f.id = %s
        """,
        [follow_up_id],
        ("project_id",),
    )


CHAT_COLUMNS = (
    "id",
    "project_id",
    "project_name",
    "chat_type_id",
    "chat_type_name",
    "title",
    "created_at",
)
_CHAT_SELECT = """
SELECT c.id, c.project_id, p.name AS project_name,
       c.chat_type_id, ct.name AS chat_type_name,
       c.title, c.created_at
FROM chats c
JOIN chat_types ct ON ct.id = c.chat_type_id
LEFT JOIN projects p ON p.id = c.project_id
"""

CHAT_MEMBER_COLUMNS = (
    "id",
    "chat_id",
    "user_id",
    "username",
    "joined_at",
)
_CHAT_MEMBER_SELECT = """
SELECT cm.id, cm.chat_id, cm.user_id, u.username, cm.joined_at
FROM chat_members cm
JOIN users u ON u.id = cm.user_id
"""

MESSAGE_COLUMNS = (
    "id",
    "chat_id",
    "chat_title",
    "project_id",
    "sender_user_id",
    "sender_username",
    "task_id",
    "task_title",
    "text",
    "created_at",
)
_MESSAGE_SELECT = """
SELECT m.id, m.chat_id, c.title AS chat_title, c.project_id,
       m.sender_user_id, sender.username AS sender_username,
       m.task_id, t.title AS task_title,
       m.text, m.created_at
FROM messages m
JOIN chats c ON c.id = m.chat_id
LEFT JOIN tasks t ON t.id = m.task_id
LEFT JOIN users sender ON sender.id = m.sender_user_id
"""

MESSAGE_RECIPIENT_COLUMNS = (
    "id",
    "message_id",
    "user_id",
    "username",
    "external_contact_id",
    "external_contact_name",
)
_MESSAGE_RECIPIENT_SELECT = """
SELECT mr.id, mr.message_id,
       mr.user_id, u.username,
       mr.external_contact_id, ec.name AS external_contact_name
FROM message_recipients mr
LEFT JOIN users u ON u.id = mr.user_id
LEFT JOIN external_contacts ec ON ec.id = mr.external_contact_id
"""


def fetch_chat_record(chat_id: int):
    """یک گفتگو را با نام نوع و پروژه می‌خواند."""
    return fetch_one(
        f"{_CHAT_SELECT} WHERE c.id = %s",
        [chat_id],
        CHAT_COLUMNS,
    )


def fetch_chats_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """گفتگوهایی را می‌خواند که کاربر عضوشان است."""
    sql = f"""
        {_CHAT_SELECT}
        JOIN chat_members cm ON cm.chat_id = c.id
        WHERE cm.user_id = %s
    """
    params = [user_id]
    if project_id is not None:
        sql += " AND c.project_id = %s"
        params.append(project_id)
    sql += " ORDER BY c.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, CHAT_COLUMNS)


def fetch_chat_membership_record(chat_id: int, user_id: int):
    """عضویت کاربر در گفتگو را برمی‌گرداند یا None."""
    return fetch_one(
        """
        SELECT id, chat_id, user_id, joined_at
        FROM chat_members
        WHERE chat_id = %s AND user_id = %s
        """,
        [chat_id, user_id],
        ("id", "chat_id", "user_id", "joined_at"),
    )


def fetch_chat_member_record(row_id: int):
    """یک عضویت گفتگو را با نام کاربر می‌خواند."""
    return fetch_one(
        f"{_CHAT_MEMBER_SELECT} WHERE cm.id = %s",
        [row_id],
        CHAT_MEMBER_COLUMNS,
    )


def fetch_chat_members_records(chat_id: int, limit: int, offset: int) -> list:
    """اعضای یک گفتگو را با صفحه‌بندی می‌خواند."""
    return fetch_many(
        f"""
        {_CHAT_MEMBER_SELECT}
        WHERE cm.chat_id = %s
        ORDER BY cm.id ASC
        LIMIT %s OFFSET %s
        """,
        [chat_id, limit, offset],
        CHAT_MEMBER_COLUMNS,
    )


def fetch_message_record(message_id: int):
    """یک پیام را با نام نوع و فرستنده می‌خواند."""
    return fetch_one(
        f"{_MESSAGE_SELECT} WHERE m.id = %s",
        [message_id],
        MESSAGE_COLUMNS,
    )


def fetch_messages_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    chat_id=None,
) -> list:
    """پیام‌های گفتگوهایی را می‌خواند که کاربر عضوشان است."""
    sql = f"""
        {_MESSAGE_SELECT}
        JOIN chat_members cm ON cm.chat_id = m.chat_id
        WHERE cm.user_id = %s
    """
    params = [user_id]
    if chat_id is not None:
        sql += " AND m.chat_id = %s"
        params.append(chat_id)
    sql += " ORDER BY m.created_at DESC, m.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, MESSAGE_COLUMNS)


def fetch_message_recipients_records(
    message_id: int,
    limit: int,
    offset: int,
) -> list:
    """گیرنده‌های یک پیام را می‌خواند."""
    return fetch_many(
        f"""
        {_MESSAGE_RECIPIENT_SELECT}
        WHERE mr.message_id = %s
        ORDER BY mr.id ASC
        LIMIT %s OFFSET %s
        """,
        [message_id, limit, offset],
        MESSAGE_RECIPIENT_COLUMNS,
    )


NOTIFICATION_COLUMNS = (
    "id",
    "user_id",
    "notification_type_id",
    "notification_type_name",
    "title",
    "message",
    "is_read",
    "created_at",
)
_NOTIFICATION_SELECT = """
SELECT n.id, n.user_id,
       n.notification_type_id, nt.name AS notification_type_name,
       n.title, n.message, n.is_read, n.created_at
FROM notifications n
JOIN notification_types nt ON nt.id = n.notification_type_id
"""

AUDIT_LOG_COLUMNS = (
    "id",
    "user_id",
    "username",
    "action",
    "entity",
    "entity_id",
    "old_value",
    "new_value",
    "created_at",
)
_AUDIT_LOG_SELECT = """
SELECT a.id, a.user_id, u.username,
       a.action, a.entity, a.entity_id,
       a.old_value, a.new_value, a.created_at
FROM audit_logs a
LEFT JOIN users u ON u.id = a.user_id
"""


def fetch_notification_record(notification_id: int):
    """یک اعلان را با نام نوع می‌خواند."""
    return fetch_one(
        f"{_NOTIFICATION_SELECT} WHERE n.id = %s",
        [notification_id],
        NOTIFICATION_COLUMNS,
    )


def fetch_notifications_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    is_read=None,
) -> list:
    """اعلان‌های همان کاربر را با صفحه‌بندی می‌خواند."""
    sql = f"{_NOTIFICATION_SELECT} WHERE n.user_id = %s"
    params = [user_id]
    if is_read is not None:
        sql += " AND n.is_read = %s"
        params.append(is_read)
    sql += " ORDER BY n.created_at DESC, n.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, NOTIFICATION_COLUMNS)


def fetch_audit_log_record(row_id: int):
    """یک ردیف ممیزی را با نام کاربری عامل می‌خواند."""
    return fetch_one(
        f"{_AUDIT_LOG_SELECT} WHERE a.id = %s",
        [row_id],
        AUDIT_LOG_COLUMNS,
    )


def fetch_audit_logs_records(
    limit: int,
    offset: int,
    entity=None,
    entity_id=None,
    user_id=None,
) -> list:
    """ردیف‌های ممیزی را با فیلتر اختیاری موجودیت و عامل می‌خواند."""
    sql = f"{_AUDIT_LOG_SELECT} WHERE 1 = 1"
    params = []
    if entity is not None:
        sql += " AND a.entity = %s"
        params.append(entity)
    if entity_id is not None:
        sql += " AND a.entity_id = %s"
        params.append(entity_id)
    if user_id is not None:
        sql += " AND a.user_id = %s"
        params.append(user_id)
    sql += " ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, AUDIT_LOG_COLUMNS)


PERFORMANCE_ACTION_COLUMNS = (
    "id",
    "user_id",
    "username",
    "project_id",
    "project_name",
    "type_id",
    "type_name",
    "type_category",
    "reason",
    "amount",
    "score",
    "financial_transaction_id",
    "created_by_user_id",
    "created_by_username",
    "created_at",
)
_PERFORMANCE_ACTION_SELECT = """
SELECT pa.id, pa.user_id, subject.username,
       pa.project_id, p.name AS project_name,
       pa.type_id, pat.name AS type_name, pat.category AS type_category,
       pa.reason, pa.amount, pa.score, pa.financial_transaction_id,
       pa.created_by_user_id, creator.username AS created_by_username,
       pa.created_at
FROM performance_actions pa
JOIN users subject ON subject.id = pa.user_id
JOIN performance_action_types pat ON pat.id = pa.type_id
JOIN users creator ON creator.id = pa.created_by_user_id
LEFT JOIN projects p ON p.id = pa.project_id
"""


def fetch_performance_action_record(row_id: int):
    """یک اقدام تشویق یا تنبیه را با نوع و نام کاربر می‌خواند."""
    return fetch_one(
        f"{_PERFORMANCE_ACTION_SELECT} WHERE pa.id = %s",
        [row_id],
        PERFORMANCE_ACTION_COLUMNS,
    )


def fetch_performance_action_records(
    limit: int,
    offset: int,
    user_id=None,
    project_id=None,
) -> list:
    """اقدام‌های تشویق و تنبیه را با فیلتر کاربر یا پروژه می‌خواند."""
    sql = f"{_PERFORMANCE_ACTION_SELECT} WHERE 1 = 1"
    params = []
    if user_id is not None:
        sql += " AND pa.user_id = %s"
        params.append(user_id)
    if project_id is not None:
        sql += " AND pa.project_id = %s"
        params.append(project_id)
    sql += " ORDER BY pa.created_at DESC, pa.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, PERFORMANCE_ACTION_COLUMNS)


def fetch_financial_account_record(account_id: int):
    """یک حساب مالی را برای وصل تراکنش نقدی می‌خواند یا None."""
    return fetch_one(
        """
        SELECT id, name, is_active
        FROM financial_accounts
        WHERE id = %s
        """,
        [account_id],
        ("id", "name", "is_active"),
    )


def insert_cash_transaction_on(connection, fields: dict):
    """تراکنش پاداش یا جریمه را درج می‌کند و ماندهٔ حساب را به‌روز می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM financial_accounts
            WHERE id = %s
            FOR UPDATE
            """,
            [fields["account_id"]],
        )
        locked = cursor.fetchone()
        if locked is None:
            return None
        cursor.execute(
            """
            INSERT INTO financial_transactions (
                account_id, project_id, user_id, category_id,
                transaction_type_id, amount, description, transaction_date
            ) VALUES (
                %(account_id)s, %(project_id)s, %(user_id)s, %(category_id)s,
                %(transaction_type_id)s, %(amount)s, %(description)s,
                CURRENT_DATE
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
        cursor.execute(
            """
            UPDATE financial_accounts
            SET balance = (
                SELECT COALESCE(SUM(amount), 0)
                FROM financial_transactions
                WHERE account_id = %s
            )
            WHERE id = %s
            """,
            [fields["account_id"], fields["account_id"]],
        )
    return int(row[0])


def sum_performance_scores_for_user(user_id: int) -> int:
    """جمع امتیازهای جدول performance_scores برای یک کاربر."""
    row = fetch_one(
        """
        SELECT COALESCE(SUM(score), 0) AS total
        FROM performance_scores
        WHERE user_id = %s
        """,
        [user_id],
        ("total",),
    )
    return int(row["total"]) if row is not None else 0


def sum_performance_action_scores_for_user(user_id: int) -> int:
    """جمع امتیازهای اقدام‌های همان کاربر؛ ردیف بدون امتیاز صفر حساب می‌شود."""
    row = fetch_one(
        """
        SELECT COALESCE(SUM(score), 0) AS total
        FROM performance_actions
        WHERE user_id = %s
        """,
        [user_id],
        ("total",),
    )
    return int(row["total"]) if row is not None else 0


def count_follow_ups_for_task(task_id: int) -> int:
    """تعداد پیگیری‌های یک وظیفه را برمی‌گرداند."""
    row = fetch_one(
        "SELECT COUNT(*) AS total FROM task_follow_ups WHERE task_id = %s",
        [task_id],
        ("total",),
    )
    return int(row["total"]) if row is not None else 0


ASSIGNABLE_USER_COLUMNS = (
    "id",
    "first_name",
    "last_name",
    "username",
    "phone",
    "is_active",
    "roles",
)


def fetch_assignable_user_records(limit: int, offset: int, registered_only: bool) -> list:
    """کاربران فعال را برای تعیین دسترسی می‌خواند.

    مدیر کل همه را می‌بیند. مدیر پروژه فقط ثبت‌نام‌شده‌های نقش کاربر را،
    بدون مدیر کل و بدون مدیر سازمان دیگر.
    """
    role_filter = ""
    if registered_only:
        role_filter = """
          AND EXISTS (
                SELECT 1
                FROM user_roles ur_member
                JOIN roles role_member ON role_member.id = ur_member.role_id
                WHERE ur_member.user_id = u.id
                  AND ur_member.is_active = true
                  AND role_member.is_active = true
                  AND role_member.name = 'کاربر'
          )
          AND NOT EXISTS (
                SELECT 1
                FROM user_roles ur_staff
                JOIN roles role_staff ON role_staff.id = ur_staff.role_id
                WHERE ur_staff.user_id = u.id
                  AND ur_staff.is_active = true
                  AND role_staff.is_active = true
                  AND role_staff.name IN ('مدیر کل', 'مدیر پروژه')
          )
        """
    return fetch_many(
        f"""
        SELECT u.id, u.first_name, u.last_name, u.username, u.phone, u.is_active,
               COALESCE(string_agg(r.name, '، ' ORDER BY r.id), '') AS roles
        FROM users u
        LEFT JOIN user_roles ur
            ON ur.user_id = u.id AND ur.is_active = true
        LEFT JOIN roles r
            ON r.id = ur.role_id AND r.is_active = true
        WHERE u.is_active = true
        {role_filter}
        GROUP BY u.id
        ORDER BY u.id DESC
        LIMIT %s OFFSET %s
        """,
        [limit, offset],
        ASSIGNABLE_USER_COLUMNS,
    )


def users_share_active_project_record(left_user_id: int, right_user_id: int) -> bool:
    """اگر هر دو عضو فعال یک پروژه باشند True است."""
    row = fetch_one(
        """
        SELECT 1 AS shared
        FROM project_members left_member
        JOIN project_members right_member
            ON right_member.project_id = left_member.project_id
        WHERE left_member.user_id = %s
          AND left_member.is_active = true
          AND right_member.user_id = %s
          AND right_member.is_active = true
        LIMIT 1
        """,
        [left_user_id, right_user_id],
        ("shared",),
    )
    return row is not None


def user_has_permission_record(user_id: int, resource: str, action: str) -> bool:
    """اگر کاربر از نقش فعال این Resource/Action را داشته باشد True است."""
    row = fetch_one(
        """
        SELECT 1 AS allowed
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        JOIN role_permissions rp ON rp.role_id = r.id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE ur.user_id = %s
          AND ur.is_active = true
          AND r.is_active = true
          AND rp.is_active = true
          AND p.resource = %s
          AND p.action = %s
        LIMIT 1
        """,
        [user_id, resource, action],
        ("allowed",),
    )
    return row is not None


def fetch_actor_record(where_sql: str, params: list):
    """بازیگر جاری را از users می‌خواند. where_sql فقط از principal ساخته می‌شود."""
    if where_sql not in {"id = %s", "username = %s"}:
        raise InvalidInputError("شرط بازیگر نامعتبر است")
    return fetch_one(
        f"SELECT id, username, is_active FROM users WHERE {where_sql}",
        params,
        ("id", "username", "is_active"),
    )


CONTENT_COLUMNS = (
    "id",
    "content_kind_id",
    "content_kind_code",
    "content_kind_name",
    "text_body",
    "media_file_id",
    "storage_key",
    "original_filename",
    "mime_type",
    "file_size_bytes",
    "duration_seconds",
    "created_by_user_id",
    "is_active",
    "created_at",
)
_CONTENT_SELECT = """
SELECT c.id, c.content_kind_id, k.code AS content_kind_code, k.name AS content_kind_name,
       c.text_body, c.media_file_id,
       mf.storage_key, mf.original_filename, mf.mime_type,
       mf.file_size_bytes, mf.duration_seconds,
       c.created_by_user_id, c.is_active, c.created_at
FROM contents c
JOIN content_kinds k ON k.id = c.content_kind_id
LEFT JOIN media_files mf ON mf.id = c.media_file_id
"""


def fetch_content_record(content_id: int):
    """یک محتوای فعال را با نوع و متادیتای فایل می‌خواند."""
    return fetch_one(
        f"{_CONTENT_SELECT} WHERE c.id = %s AND c.is_active",
        [content_id],
        CONTENT_COLUMNS,
    )


def fetch_contents_for_actor_records(actor_id: int, limit: int, offset: int) -> list:
    """محتواهای فعال سازنده را از جدید به قدیم می‌خواند."""
    return fetch_many(
        f"{_CONTENT_SELECT} WHERE c.created_by_user_id = %s AND c.is_active "
        "ORDER BY c.id DESC LIMIT %s OFFSET %s",
        [actor_id, limit, offset],
        CONTENT_COLUMNS,
    )


TEXT_ANALYSIS_COLUMNS = (
    "id",
    "source_type_id",
    "source_type",
    "source_id",
    "model",
    "created_by_user_id",
    "project_id",
    "created_at",
)
_TEXT_ANALYSIS_SELECT = """
SELECT a.id, a.source_type_id, st.code AS source_type, a.source_id,
       a.model, a.created_by_user_id, a.project_id, a.created_at
FROM text_analyses a
JOIN analysis_source_types st ON st.id = a.source_type_id
"""

TEXT_ANALYSIS_LIST_COLUMNS = TEXT_ANALYSIS_COLUMNS + (
    "mention_count",
    "topic_count",
    "has_sentiment",
    "discourse_count",
    "intent_count",
    "rhetoric_count",
    "fact_count",
    "quote_count",
    "keyword_count",
)

KEYWORD_HIT_COLUMNS = (
    "id",
    "keyword_id",
    "phrase",
    "mention_text",
    "start_offset",
    "end_offset",
    "confidence",
    "source_type",
    "source_id",
    "project_id",
    "created_by_user_id",
)

MENTION_COLUMNS = (
    "id",
    "entity_id",
    "type",
    "canonical_name",
    "normalized_name",
    "status",
    "mention_text",
    "start_offset",
    "end_offset",
    "confidence",
    "occurred_at",
)

TOPIC_HIT_COLUMNS = (
    "id",
    "topic_id",
    "code",
    "name",
    "level",
    "parent_code",
    "is_primary",
    "confidence",
    "mention_text",
)

SENTIMENT_COLUMNS = (
    "id",
    "polarity",
    "polarity_name",
    "intensity",
    "intensity_name",
    "intensity_level",
    "mention_text",
)

EMOTION_COLUMNS = (
    "id",
    "emotion",
    "name",
    "intensity",
    "intensity_name",
    "intensity_level",
    "mention_text",
)

ENTITY_HIT_COLUMNS = (
    "id",
    "type",
    "canonical_name",
    "normalized_name",
    "status",
    "mention_count",
)

SPEECH_HIT_COLUMNS = (
    "id",
    "code",
    "name",
    "is_primary",
    "confidence",
    "mention_text",
)

DISCOURSE_HIT_COLUMNS = SPEECH_HIT_COLUMNS + ("is_discovered",)

INTENT_SLOT_COLUMNS = (
    "id",
    "analysis_intent_id",
    "slot_name",
    "slot_value",
)

DISCOURSE_SLOT_COLUMNS = (
    "id",
    "analysis_discourse_id",
    "slot_name",
    "slot_value",
)

RHETORIC_HIT_COLUMNS = SPEECH_HIT_COLUMNS + ("intended_meaning",)

RHETORIC_SLOT_COLUMNS = (
    "id",
    "analysis_rhetoric_id",
    "slot_name",
    "slot_value",
)

FACT_HIT_COLUMNS = (
    "id",
    "fact_id",
    "kind",
    "kind_name",
    "name",
    "value",
    "unit",
    "unit_name",
    "role",
    "role_name",
    "grounding",
    "grounding_name",
    "derivation",
    "derivation_name",
    "effect",
    "previous",
    "current",
    "mention_text",
    "start_offset",
    "end_offset",
    "evidence_texts",
    "source_ids",
    "confidence",
)

QUOTE_HIT_COLUMNS = (
    "id",
    "mode",
    "mode_name",
    "attributed_to",
    "quoted_text",
    "mention_text",
    "start_offset",
    "end_offset",
    "confidence",
)

SOURCE_ACCESS_COLUMNS = (
    "source_type",
    "source_id",
    "project_id",
    "chat_id",
    "manager_user_id",
    "visibility",
    "created_by_user_id",
)


def fetch_text_analysis_record(analysis_id: int):
    """یک اجرای تحلیل را با کد منبع می‌خواند."""
    return fetch_one(
        f"{_TEXT_ANALYSIS_SELECT} WHERE a.id = %s",
        [analysis_id],
        TEXT_ANALYSIS_COLUMNS,
    )


def fetch_text_analyses_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    source_type=None,
    source_id=None,
) -> list:
    """تحلیل‌هایی را می‌خواند که همین کاربر ساخته است."""
    filters = ["a.created_by_user_id = %s"]
    params = [user_id]
    if source_type is not None:
        filters.append("st.code = %s")
        params.append(source_type)
    if source_id is not None:
        filters.append("a.source_id = %s")
        params.append(source_id)
    where_sql = " AND ".join(filters)
    params.extend([limit, offset])
    return fetch_many(
        f"""
        SELECT a.id, a.source_type_id, st.code AS source_type, a.source_id,
               a.model, a.created_by_user_id, a.project_id, a.created_at,
               COALESCE(mentions.mention_count, 0) AS mention_count,
               COALESCE(topics.topic_count, 0) AS topic_count,
               COALESCE(stance.has_sentiment, false) AS has_sentiment,
               COALESCE(discourses.discourse_count, 0) AS discourse_count,
               COALESCE(intents.intent_count, 0) AS intent_count,
               COALESCE(rhetorics.rhetoric_count, 0) AS rhetoric_count,
               COALESCE(facts.fact_count, 0) AS fact_count,
               COALESCE(quotes.quote_count, 0) AS quote_count,
               COALESCE(keywords.keyword_count, 0) AS keyword_count
        FROM text_analyses a
        JOIN analysis_source_types st ON st.id = a.source_type_id
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS mention_count
            FROM entity_mentions m
            WHERE m.analysis_id = a.id
        ) mentions ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS topic_count
            FROM text_analysis_topics t
            WHERE t.analysis_id = a.id
        ) topics ON true
        LEFT JOIN LATERAL (
            SELECT EXISTS (
                SELECT 1 FROM text_analysis_sentiments s
                WHERE s.analysis_id = a.id
            ) AS has_sentiment
        ) stance ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS discourse_count
            FROM text_analysis_discourses d
            WHERE d.analysis_id = a.id
        ) discourses ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS intent_count
            FROM text_analysis_intents i
            WHERE i.analysis_id = a.id
        ) intents ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS rhetoric_count
            FROM text_analysis_rhetorics r
            WHERE r.analysis_id = a.id
        ) rhetorics ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS fact_count
            FROM text_analysis_facts f
            WHERE f.analysis_id = a.id
        ) facts ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS quote_count
            FROM text_analysis_quotes q
            WHERE q.analysis_id = a.id
        ) quotes ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS keyword_count
            FROM keyword_mentions k
            WHERE k.analysis_id = a.id
        ) keywords ON true
        WHERE {where_sql}
        ORDER BY a.id DESC
        LIMIT %s OFFSET %s
        """,
        params,
        TEXT_ANALYSIS_LIST_COLUMNS,
    )


def fetch_text_analysis_keywords_records(analysis_id: int) -> list:
    """کلمات کلیدی یک تحلیل را با متن خام، پروژه و صاحب متن می‌خواند."""
    return fetch_many(
        """
        SELECT km.id, km.keyword_id, k.phrase, km.mention_text,
               COALESCE(km.start_offset, -1) AS start_offset,
               COALESCE(km.end_offset, -1) AS end_offset,
               km.confidence, st.code AS source_type, km.source_id,
               km.project_id, km.created_by_user_id
        FROM keyword_mentions km
        JOIN keywords k ON k.id = km.keyword_id
        JOIN analysis_source_types st ON st.id = km.source_type_id
        WHERE km.analysis_id = %s
        ORDER BY km.id
        """,
        [analysis_id],
        KEYWORD_HIT_COLUMNS,
    )


def fetch_text_analysis_mentions_records(analysis_id: int) -> list:
    """ذکرهای یک تحلیل را با نوع و زمان اختیاری می‌خواند."""
    return fetch_many(
        """
        SELECT m.id, m.entity_id, et.code AS type,
               e.canonical_name, e.normalized_name, es.code AS status,
               m.mention_text, m.start_offset, m.end_offset, m.confidence,
               t.occurred_at
        FROM entity_mentions m
        JOIN entities e ON e.id = m.entity_id
        JOIN entity_types et ON et.id = e.entity_type_id
        JOIN entity_statuses es ON es.id = e.status_id
        LEFT JOIN entity_mention_times t ON t.mention_id = m.id
        WHERE m.analysis_id = %s
        ORDER BY m.start_offset, m.id
        """,
        [analysis_id],
        MENTION_COLUMNS,
    )


def fetch_text_analysis_topics_records(analysis_id: int) -> list:
    """موضوع‌های یک تحلیل را با کد و نام می‌خواند."""
    return fetch_many(
        """
        SELECT tat.id, tp.id AS topic_id, tp.code, tp.name, tp.level,
               parent.code AS parent_code, tat.is_primary, tat.confidence,
               tat.mention_text
        FROM text_analysis_topics tat
        JOIN topics tp ON tp.id = tat.topic_id
        LEFT JOIN topics parent ON parent.id = tp.parent_id
        WHERE tat.analysis_id = %s
        ORDER BY tat.is_primary DESC, tp.level, tat.id
        """,
        [analysis_id],
        TOPIC_HIT_COLUMNS,
    )


def fetch_text_analysis_sentiment_record(analysis_id: int):
    """قطبیت یک تحلیل را می‌خواند یا None."""
    return fetch_one(
        """
        SELECT s.id, p.code AS polarity, p.name AS polarity_name,
               i.code AS intensity, i.name AS intensity_name, i.level AS intensity_level,
               s.mention_text
        FROM text_analysis_sentiments s
        JOIN polarities p ON p.id = s.polarity_id
        JOIN intensity_levels i ON i.id = s.intensity_id
        WHERE s.analysis_id = %s
        """,
        [analysis_id],
        SENTIMENT_COLUMNS,
    )


def fetch_text_analysis_emotions_records(analysis_id: int) -> list:
    """هیجان‌های یک تحلیل را می‌خواند."""
    return fetch_many(
        """
        SELECT te.id, e.code AS emotion, e.name,
               i.code AS intensity, i.name AS intensity_name, i.level AS intensity_level,
               te.mention_text
        FROM text_analysis_emotions te
        JOIN emotions e ON e.id = te.emotion_id
        JOIN intensity_levels i ON i.id = te.intensity_id
        WHERE te.analysis_id = %s
        ORDER BY te.id
        """,
        [analysis_id],
        EMOTION_COLUMNS,
    )


def fetch_text_analysis_discourses_records(analysis_id: int) -> list:
    """ژانرهای یک تحلیل را با کد و نام می‌خواند."""
    return fetch_many(
        """
        SELECT tad.id, dt.code, dt.name, tad.is_primary, tad.confidence,
               tad.mention_text, dt.is_discovered
        FROM text_analysis_discourses tad
        JOIN discourse_types dt ON dt.id = tad.discourse_type_id
        WHERE tad.analysis_id = %s
        ORDER BY tad.is_primary DESC, tad.id
        """,
        [analysis_id],
        DISCOURSE_HIT_COLUMNS,
    )


def fetch_text_analysis_intents_records(analysis_id: int) -> list:
    """نیت‌های یک تحلیل را با کد و نام می‌خواند."""
    return fetch_many(
        """
        SELECT tai.id, it.code, it.name, tai.is_primary, tai.confidence,
               tai.mention_text
        FROM text_analysis_intents tai
        JOIN intents it ON it.id = tai.intent_id
        WHERE tai.analysis_id = %s
        ORDER BY tai.is_primary DESC, tai.id
        """,
        [analysis_id],
        SPEECH_HIT_COLUMNS,
    )


def fetch_text_analysis_intent_slots_records(analysis_id: int) -> list:
    """اجزای نیت‌های یک تحلیل را می‌خواند."""
    return fetch_many(
        """
        SELECT s.id, s.analysis_intent_id, s.slot_name, s.slot_value
        FROM text_analysis_intent_slots s
        JOIN text_analysis_intents tai ON tai.id = s.analysis_intent_id
        WHERE tai.analysis_id = %s
        ORDER BY s.analysis_intent_id, s.id
        """,
        [analysis_id],
        INTENT_SLOT_COLUMNS,
    )


def fetch_text_analysis_discourse_slots_records(analysis_id: int) -> list:
    """نقش‌های ژانرهای یک تحلیل را می‌خواند."""
    return fetch_many(
        """
        SELECT s.id, s.analysis_discourse_id, s.slot_name, s.slot_value
        FROM text_analysis_discourse_slots s
        JOIN text_analysis_discourses tad ON tad.id = s.analysis_discourse_id
        WHERE tad.analysis_id = %s
        ORDER BY s.analysis_discourse_id, s.id
        """,
        [analysis_id],
        DISCOURSE_SLOT_COLUMNS,
    )


def fetch_text_analysis_rhetorics_records(analysis_id: int) -> list:
    """صنعت‌های بیان یک تحلیل را با کد و نام می‌خواند."""
    return fetch_many(
        """
        SELECT tar.id, rt.code, rt.name, tar.is_primary, tar.confidence,
               tar.mention_text, tar.intended_meaning
        FROM text_analysis_rhetorics tar
        JOIN rhetoric_types rt ON rt.id = tar.rhetoric_type_id
        WHERE tar.analysis_id = %s
        ORDER BY tar.is_primary DESC, tar.id
        """,
        [analysis_id],
        RHETORIC_HIT_COLUMNS,
    )


def fetch_text_analysis_rhetoric_slots_records(analysis_id: int) -> list:
    """نقش‌های صنعت بیان یک تحلیل را می‌خواند."""
    return fetch_many(
        """
        SELECT s.id, s.analysis_rhetoric_id, s.slot_name, s.slot_value
        FROM text_analysis_rhetoric_slots s
        JOIN text_analysis_rhetorics tar ON tar.id = s.analysis_rhetoric_id
        WHERE tar.analysis_id = %s
        ORDER BY s.analysis_rhetoric_id, s.id
        """,
        [analysis_id],
        RHETORIC_SLOT_COLUMNS,
    )


def fetch_text_analysis_facts_records(analysis_id: int) -> list:
    """فکت‌های یک تحلیل را با نوع و نقش و صراحت می‌خواند."""
    return fetch_many(
        """
        SELECT taf.id, taf.fact_code AS fact_id, fk.code AS kind, fk.name AS kind_name,
               taf.name, taf.value, fu.code AS unit, fu.name AS unit_name,
               fr.code AS role, fr.name AS role_name,
               fg.code AS grounding, fg.name AS grounding_name,
               COALESCE(fd.code, '') AS derivation, COALESCE(fd.name, '') AS derivation_name,
               taf.effect, taf.previous, taf.current, taf.mention_text,
               COALESCE(taf.start_offset, -1) AS start_offset,
               COALESCE(taf.end_offset, -1) AS end_offset,
               taf.evidence_texts, taf.source_ids, taf.confidence
        FROM text_analysis_facts taf
        JOIN fact_kinds fk ON fk.id = taf.kind_id
        JOIN fact_quantity_roles fr ON fr.id = taf.role_id
        JOIN fact_groundings fg ON fg.id = taf.grounding_id
        LEFT JOIN fact_units fu ON fu.id = taf.unit_id
        LEFT JOIN fact_derivations fd ON fd.id = taf.derivation_id
        WHERE taf.analysis_id = %s
        ORDER BY taf.id
        """,
        [analysis_id],
        FACT_HIT_COLUMNS,
    )


def fetch_text_analysis_quotes_records(analysis_id: int) -> list:
    """نقل‌قول‌های یک تحلیل را با شیوه و گوینده و شاهد می‌خواند."""
    return fetch_many(
        """
        SELECT taq.id, qm.code AS mode, qm.name AS mode_name,
               taq.attributed_to, taq.quoted_text, taq.mention_text,
               COALESCE(taq.start_offset, -1) AS start_offset,
               COALESCE(taq.end_offset, -1) AS end_offset,
               taq.confidence
        FROM text_analysis_quotes taq
        JOIN quote_modes qm ON qm.id = taq.mode_id
        WHERE taq.analysis_id = %s
        ORDER BY taq.id
        """,
        [analysis_id],
        QUOTE_HIT_COLUMNS,
    )


def fetch_text_analysis_entities_records(analysis_id: int) -> list:
    """موجودیت‌های canonical ذکرشده در همین تحلیل را می‌خواند."""
    return fetch_many(
        """
        SELECT e.id, et.code AS type, e.canonical_name, e.normalized_name,
               es.code AS status, COUNT(m.id) AS mention_count
        FROM entity_mentions m
        JOIN entities e ON e.id = m.entity_id
        JOIN entity_types et ON et.id = e.entity_type_id
        JOIN entity_statuses es ON es.id = e.status_id
        WHERE m.analysis_id = %s
        GROUP BY e.id, et.code, e.canonical_name, e.normalized_name, es.code
        ORDER BY et.code, e.canonical_name
        """,
        [analysis_id],
        ENTITY_HIT_COLUMNS,
    )


def fetch_source_access_record(source_type: str, source_id: int):
    """فیلدهای دسترسی منبع عملیاتی تحلیل را می‌خواند یا None."""
    if source_type == "message":
        return fetch_one(
            """
            SELECT 'message' AS source_type, m.id AS source_id,
                   c.project_id, m.chat_id,
                   NULL::integer AS manager_user_id,
                   NULL::varchar AS visibility, m.sender_user_id AS created_by_user_id
            FROM messages m
            JOIN chats c ON c.id = m.chat_id
            WHERE m.id = %s
            """,
            [source_id],
            SOURCE_ACCESS_COLUMNS,
        )
    if source_type == "meeting":
        return fetch_one(
            """
            SELECT 'meeting' AS source_type, mt.id AS source_id, mt.project_id,
                   NULL::integer AS chat_id, mt.manager_user_id, mt.visibility,
                   mt.manager_user_id AS created_by_user_id
            FROM meetings mt
            WHERE mt.id = %s
            """,
            [source_id],
            SOURCE_ACCESS_COLUMNS,
        )
    if source_type == "content":
        return fetch_one(
            """
            SELECT 'content' AS source_type, c.id AS source_id,
                   pd.project_id, NULL::integer AS chat_id,
                   NULL::integer AS manager_user_id, NULL::varchar AS visibility,
                   c.created_by_user_id
            FROM contents c
            LEFT JOIN project_documents pd
                ON pd.content_id = c.id AND pd.is_active
            WHERE c.id = %s AND c.is_active
            """,
            [source_id],
            SOURCE_ACCESS_COLUMNS,
        )
    return None


def fetch_meeting_participant_record(meeting_id: int, user_id: int):
    """عضویت کاربر در جلسه را می‌خواند یا None."""
    return fetch_one(
        """
        SELECT id
        FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        LIMIT 1
        """,
        [meeting_id, user_id],
        ("id",),
    )


ISSUE_COLUMNS = (
    "id",
    "project_id",
    "project_name",
    "title",
    "status_id",
    "status_code",
    "status_name",
    "created_by_user_id",
    "created_at",
)
_ISSUE_SELECT = """
SELECT i.id, i.project_id, p.name AS project_name, i.title,
       i.status_id, st.code AS status_code, st.name AS status_name,
       i.created_by_user_id, i.created_at
FROM issues i
JOIN projects p ON p.id = i.project_id
JOIN issue_statuses st ON st.id = i.status_id
"""

ISSUE_SOURCE_COLUMNS = (
    "id",
    "analysis_id",
    "source_type",
    "source_id",
)


def fetch_issue_record(issue_id: int):
    """یک مسئله را با نام پروژه و وضعیت می‌خواند."""
    return fetch_one(
        f"{_ISSUE_SELECT} WHERE i.id = %s",
        [issue_id],
        ISSUE_COLUMNS,
    )


def fetch_issues_for_actor_records(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """مسائل پروژه‌هایی را می‌خواند که کاربر عضو فعال‌شان است."""
    sql = f"""
        {_ISSUE_SELECT}
        JOIN project_members pm ON pm.project_id = i.project_id
        WHERE pm.user_id = %s AND pm.is_active = true
    """
    params = [user_id]
    if project_id is not None:
        sql += " AND i.project_id = %s"
        params.append(project_id)
    sql += " ORDER BY i.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return fetch_many(sql, params, ISSUE_COLUMNS)


def fetch_issue_source_records(issue_id: int) -> list:
    """منابع تحلیل وصل‌شده به یک مسئله را می‌خواند."""
    return fetch_many(
        """
        SELECT s.id, s.analysis_id, st.code AS source_type, a.source_id
        FROM issue_sources s
        JOIN text_analyses a ON a.id = s.analysis_id
        JOIN analysis_source_types st ON st.id = a.source_type_id
        WHERE s.issue_id = %s
        ORDER BY s.id
        """,
        [issue_id],
        ISSUE_SOURCE_COLUMNS,
    )


ISSUE_CAUSE_COLUMNS = (
    "id",
    "issue_id",
    "cause_issue_id",
    "cause_title",
    "cause_level_id",
    "cause_level_code",
    "cause_level_name",
    "cause_level",
)
_ISSUE_CAUSE_SELECT = """
SELECT c.id, c.issue_id, c.cause_issue_id, cause.title AS cause_title,
       c.cause_level_id, cl.code AS cause_level_code, cl.name AS cause_level_name,
       cl.level AS cause_level
FROM issue_causes c
JOIN issues cause ON cause.id = c.cause_issue_id
JOIN cause_levels cl ON cl.id = c.cause_level_id
"""


def fetch_issue_cause_record(row_id: int):
    """یک حلقهٔ علت را با عنوان مسئلهٔ علت و سطح می‌خواند."""
    return fetch_one(
        f"{_ISSUE_CAUSE_SELECT} WHERE c.id = %s",
        [row_id],
        ISSUE_CAUSE_COLUMNS,
    )


def fetch_issue_cause_records(issue_id: int) -> list:
    """علت‌های مستقیم یک مسئله را به ترتیب عمق می‌خواند."""
    return fetch_many(
        f"{_ISSUE_CAUSE_SELECT} WHERE c.issue_id = %s ORDER BY cl.level, c.id",
        [issue_id],
        ISSUE_CAUSE_COLUMNS,
    )


def fetch_issue_in_project_by_title_record(project_id: int, title: str):
    """جدیدترین مسئلهٔ همین پروژه با همین عنوان را می‌خواند یا None."""
    return fetch_one(
        f"{_ISSUE_SELECT} WHERE i.project_id = %s AND i.title = %s "
        "ORDER BY i.id DESC LIMIT 1",
        [project_id, title],
        ISSUE_COLUMNS,
    )


ISSUE_TASK_COLUMNS = (
    "id",
    "issue_id",
    "task_id",
    "task_title",
)
_ISSUE_TASK_SELECT = """
SELECT it.id, it.issue_id, it.task_id, t.title AS task_title
FROM issue_tasks it
JOIN tasks t ON t.id = it.task_id
"""


def fetch_issue_task_record(row_id: int):
    """یک حلقهٔ مسئله-وظیفه را با عنوان کار می‌خواند."""
    return fetch_one(
        f"{_ISSUE_TASK_SELECT} WHERE it.id = %s",
        [row_id],
        ISSUE_TASK_COLUMNS,
    )


def fetch_issue_task_records(issue_id: int) -> list:
    """وظیفه‌های وصل‌شده به یک مسئله را می‌خواند."""
    return fetch_many(
        f"{_ISSUE_TASK_SELECT} WHERE it.issue_id = %s ORDER BY it.id",
        [issue_id],
        ISSUE_TASK_COLUMNS,
    )


ISSUE_IMPORTANCE_COLUMNS = (
    "id",
    "issue_id",
    "importance_id",
    "importance_name",
)
_ISSUE_IMPORTANCE_SELECT = """
SELECT ii.id, ii.issue_id, ii.importance_id, ti.name AS importance_name
FROM issue_importances ii
JOIN task_importances ti ON ti.id = ii.importance_id
"""

ISSUE_URGENCY_COLUMNS = (
    "id",
    "issue_id",
    "priority_id",
    "priority_name",
)
_ISSUE_URGENCY_SELECT = """
SELECT iu.id, iu.issue_id, iu.priority_id, tp.name AS priority_name
FROM issue_urgencies iu
JOIN task_priorities tp ON tp.id = iu.priority_id
"""

ISSUE_SEVERITY_COLUMNS = (
    "id",
    "issue_id",
    "severity_id",
    "severity_code",
    "severity_name",
)
_ISSUE_SEVERITY_SELECT = """
SELECT ise.id, ise.issue_id, ise.severity_id,
       sl.code AS severity_code, sl.name AS severity_name
FROM issue_severities ise
JOIN severity_levels sl ON sl.id = ise.severity_id
"""

ISSUE_IMPACT_COLUMNS = (
    "id",
    "issue_id",
    "impact_type_id",
    "impact_type_code",
    "impact_type_name",
    "description",
)
_ISSUE_IMPACT_SELECT = """
SELECT ip.id, ip.issue_id, ip.impact_type_id,
       it.code AS impact_type_code, it.name AS impact_type_name, ip.description
FROM issue_impacts ip
JOIN impact_types it ON it.id = ip.impact_type_id
"""


def fetch_issue_importance_record(issue_id: int):
    """اهمیت یک مسئله را می‌خواند یا None."""
    return fetch_one(
        f"{_ISSUE_IMPORTANCE_SELECT} WHERE ii.issue_id = %s",
        [issue_id],
        ISSUE_IMPORTANCE_COLUMNS,
    )


def fetch_issue_importance_by_id_record(row_id: int):
    """یک ردیف اهمیت مسئله را با شناسه می‌خواند."""
    return fetch_one(
        f"{_ISSUE_IMPORTANCE_SELECT} WHERE ii.id = %s",
        [row_id],
        ISSUE_IMPORTANCE_COLUMNS,
    )


def fetch_issue_urgency_record(issue_id: int):
    """فوریت یک مسئله را می‌خواند یا None."""
    return fetch_one(
        f"{_ISSUE_URGENCY_SELECT} WHERE iu.issue_id = %s",
        [issue_id],
        ISSUE_URGENCY_COLUMNS,
    )


def fetch_issue_urgency_by_id_record(row_id: int):
    """یک ردیف فوریت مسئله را با شناسه می‌خواند."""
    return fetch_one(
        f"{_ISSUE_URGENCY_SELECT} WHERE iu.id = %s",
        [row_id],
        ISSUE_URGENCY_COLUMNS,
    )


def fetch_issue_severity_record(issue_id: int):
    """شدت یک مسئله را می‌خواند یا None."""
    return fetch_one(
        f"{_ISSUE_SEVERITY_SELECT} WHERE ise.issue_id = %s",
        [issue_id],
        ISSUE_SEVERITY_COLUMNS,
    )


def fetch_issue_severity_by_id_record(row_id: int):
    """یک ردیف شدت مسئله را با شناسه می‌خواند."""
    return fetch_one(
        f"{_ISSUE_SEVERITY_SELECT} WHERE ise.id = %s",
        [row_id],
        ISSUE_SEVERITY_COLUMNS,
    )


def fetch_issue_impact_record(row_id: int):
    """یک اثر مسئله را با نوع seed می‌خواند."""
    return fetch_one(
        f"{_ISSUE_IMPACT_SELECT} WHERE ip.id = %s",
        [row_id],
        ISSUE_IMPACT_COLUMNS,
    )


def fetch_issue_impact_records(issue_id: int) -> list:
    """اثرهای یک مسئله را می‌خواند."""
    return fetch_many(
        f"{_ISSUE_IMPACT_SELECT} WHERE ip.issue_id = %s ORDER BY ip.id",
        [issue_id],
        ISSUE_IMPACT_COLUMNS,
    )


ISSUE_TOPIC_COLUMNS = (
    "id",
    "issue_id",
    "topic_id",
    "topic_code",
    "topic_name",
    "topic_level",
)
_ISSUE_TOPIC_SELECT = """
SELECT it.id, it.issue_id, it.topic_id, tp.code AS topic_code,
       tp.name AS topic_name, tp.level AS topic_level
FROM issue_topics it
JOIN topics tp ON tp.id = it.topic_id
"""

ISSUE_ENTITY_COLUMNS = (
    "id",
    "issue_id",
    "entity_id",
    "canonical_name",
    "entity_type",
    "role_id",
    "role_code",
    "role_name",
)
_ISSUE_ENTITY_SELECT = """
SELECT ie.id, ie.issue_id, ie.entity_id, e.canonical_name,
       et.code AS entity_type, ie.role_id, r.code AS role_code, r.name AS role_name
FROM issue_entities ie
JOIN entities e ON e.id = ie.entity_id
JOIN entity_types et ON et.id = e.entity_type_id
JOIN issue_entity_roles r ON r.id = ie.role_id
"""


def fetch_issue_topic_record(row_id: int):
    """یک حلقهٔ مسئله-موضوع را می‌خواند."""
    return fetch_one(
        f"{_ISSUE_TOPIC_SELECT} WHERE it.id = %s",
        [row_id],
        ISSUE_TOPIC_COLUMNS,
    )


def fetch_issue_topic_records(issue_id: int) -> list:
    """موضوع‌های وصل‌شده به یک مسئله را می‌خواند."""
    return fetch_many(
        f"{_ISSUE_TOPIC_SELECT} WHERE it.issue_id = %s ORDER BY tp.level, it.id",
        [issue_id],
        ISSUE_TOPIC_COLUMNS,
    )


def fetch_issue_entity_record(row_id: int):
    """یک حلقهٔ مسئله-موجودیت را با نقش می‌خواند."""
    return fetch_one(
        f"{_ISSUE_ENTITY_SELECT} WHERE ie.id = %s",
        [row_id],
        ISSUE_ENTITY_COLUMNS,
    )


def fetch_issue_entity_records(issue_id: int) -> list:
    """موجودیت‌های وصل‌شده به یک مسئله را می‌خواند."""
    return fetch_many(
        f"{_ISSUE_ENTITY_SELECT} WHERE ie.issue_id = %s ORDER BY ie.id",
        [issue_id],
        ISSUE_ENTITY_COLUMNS,
    )


def issue_source_has_topic_record(issue_id: int, topic_id: int):
    """اگر موضوع روی یکی از تحلیل‌های مبدأ مسئله باشد ردیف برمی‌گرداند."""
    return fetch_one(
        """
        SELECT tat.id
        FROM text_analysis_topics tat
        JOIN issue_sources s ON s.analysis_id = tat.analysis_id
        WHERE s.issue_id = %s AND tat.topic_id = %s
        LIMIT 1
        """,
        [issue_id, topic_id],
        ("id",),
    )


def issue_source_has_entity_record(issue_id: int, entity_id: int):
    """اگر موجودیت در ذکرهای تحلیل مبدأ مسئله باشد ردیف برمی‌گرداند."""
    return fetch_one(
        """
        SELECT m.id
        FROM entity_mentions m
        JOIN issue_sources s ON s.analysis_id = m.analysis_id
        WHERE s.issue_id = %s AND m.entity_id = %s
        LIMIT 1
        """,
        [issue_id, entity_id],
        ("id",),
    )


__all__ = [
    "count_follow_ups_for_task",
    "fetch_active_membership_record",
    "fetch_actor_record",
    "fetch_audit_log_record",
    "fetch_audit_logs_records",
    "fetch_chat_member_record",
    "fetch_chat_members_records",
    "fetch_chat_membership_record",
    "fetch_chat_record",
    "fetch_chats_for_actor_records",
    "fetch_content_record",
    "fetch_text_analysis_record",
    "fetch_text_analyses_for_actor_records",
    "fetch_text_analysis_mentions_records",
    "fetch_text_analysis_keywords_records",
    "fetch_text_analysis_topics_records",
    "fetch_text_analysis_sentiment_record",
    "fetch_text_analysis_emotions_records",
    "fetch_text_analysis_entities_records",
    "fetch_text_analysis_discourses_records",
    "fetch_text_analysis_intents_records",
    "fetch_text_analysis_intent_slots_records",
    "fetch_text_analysis_discourse_slots_records",
    "fetch_text_analysis_rhetorics_records",
    "fetch_text_analysis_rhetoric_slots_records",
    "fetch_text_analysis_facts_records",
    "fetch_text_analysis_quotes_records",
    "fetch_source_access_record",
    "fetch_meeting_participant_record",
    "fetch_follow_up_project_id_record",
    "fetch_follow_up_record",
    "fetch_follow_ups_for_task_records",
    "fetch_issue_record",
    "fetch_issues_for_actor_records",
    "fetch_issue_source_records",
    "fetch_issue_cause_record",
    "fetch_issue_cause_records",
    "fetch_issue_in_project_by_title_record",
    "fetch_issue_task_record",
    "fetch_issue_task_records",
    "fetch_issue_importance_record",
    "fetch_issue_importance_by_id_record",
    "fetch_issue_urgency_record",
    "fetch_issue_urgency_by_id_record",
    "fetch_issue_severity_record",
    "fetch_issue_severity_by_id_record",
    "fetch_issue_impact_record",
    "fetch_issue_impact_records",
    "fetch_issue_topic_record",
    "fetch_issue_topic_records",
    "fetch_issue_entity_record",
    "fetch_issue_entity_records",
    "issue_source_has_topic_record",
    "issue_source_has_entity_record",
    "fetch_member_record",
    "fetch_members_for_project_records",
    "fetch_message_record",
    "fetch_message_recipients_records",
    "fetch_messages_for_actor_records",
    "fetch_notification_record",
    "fetch_notifications_for_actor_records",
    "fetch_financial_account_record",
    "fetch_performance_action_record",
    "fetch_performance_action_records",
    "fetch_project_record",
    "fetch_projects_for_actor_records",
    "fetch_role_permission_records",
    "fetch_next_task_item_sort_order",
    "fetch_task_item_project_id_record",
    "fetch_task_item_record",
    "fetch_task_items_for_task_records",
    "fetch_task_record",
    "fetch_tasks_for_actor_records",
    "fetch_user_role_records",
    "insert_cash_transaction_on",
    "sum_performance_action_scores_for_user",
    "sum_performance_scores_for_user",
    "user_has_permission_record",
]
