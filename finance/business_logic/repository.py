"""کوئری‌های حساب، تراکنش، و دستهٔ مالی.

ماندهٔ حساب از SUM تراکنش‌ها نوشته می‌شود، نه مقدار دستی.
حذف تراکنش اینجا نیست.
"""

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from errors.crud import InvalidInputError
from repository.db import fetch_many, fetch_one, run_query

_LOOKUP_TABLES = {
    "financial_account_types": "نوع حساب",
    "transaction_types": "نوع تراکنش",
    "financial_categories": "دسته مالی",
}

ACCOUNT_COLUMNS = (
    "id",
    "name",
    "account_type_id",
    "account_type_name",
    "balance",
    "is_active",
)

_ACCOUNT_SELECT = """
SELECT a.id, a.name, a.account_type_id, t.name AS account_type_name,
       a.balance, a.is_active
FROM financial_accounts a
JOIN financial_account_types t ON t.id = a.account_type_id
"""

TRANSACTION_COLUMNS = (
    "id",
    "account_id",
    "account_name",
    "project_id",
    "user_id",
    "category_id",
    "category_name",
    "transaction_type_id",
    "transaction_type_name",
    "amount",
    "description",
    "transaction_date",
    "created_at",
)

_TRANSACTION_SELECT = """
SELECT tx.id, tx.account_id, a.name AS account_name,
       tx.project_id, tx.user_id,
       tx.category_id, c.name AS category_name,
       tx.transaction_type_id, tt.name AS transaction_type_name,
       tx.amount, tx.description, tx.transaction_date, tx.created_at
FROM financial_transactions tx
JOIN financial_accounts a ON a.id = tx.account_id
JOIN transaction_types tt ON tt.id = tx.transaction_type_id
LEFT JOIN financial_categories c ON c.id = tx.category_id
"""

CATEGORY_COLUMNS = (
    "id",
    "name",
    "description",
)

UNIQUE_MESSAGES = {
    "financial_categories_name_key": "این نام دسته از قبل هست",
    "financial_account_types_name_key": "این نام نوع حساب از قبل هست",
}


def resolve_lookup_id(table: str, lookup_id, name) -> int:
    """شناسه یک ردیف lookup را از شناسه یا نام برمی‌گرداند."""
    label = _LOOKUP_TABLES.get(table)
    if label is None:
        raise InvalidInputError("جدول lookup نامعتبر است")
    if lookup_id is not None:
        column = "id"
        param = lookup_id
    else:
        if not name:
            raise InvalidInputError(f"{label} لازم است")
        column = "name"
        param = name

    def work(connection):
        query = sql.SQL("SELECT * FROM {} WHERE {} = %s LIMIT 1").format(
            sql.Identifier(table),
            sql.Identifier(column),
        )
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, [param])
            found = cursor.fetchone()
        if found is None:
            return None
        return dict(found)

    row = run_query(work)
    if row is None:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
        raise InvalidInputError(f"{label} «{name}» پیدا نشد")
    if row.get("is_active") is False:
        if lookup_id is not None:
            raise InvalidInputError(f"{label} غیرفعال است")
        raise InvalidInputError(f"{label} «{name}» غیرفعال است")
    return int(row["id"])


def fetch_lookup_name(table: str, lookup_id: int) -> str:
    """نام یک ردیف lookup را با شناسه می‌خواند."""
    label = _LOOKUP_TABLES.get(table)
    if label is None:
        raise InvalidInputError("جدول lookup نامعتبر است")

    def work(connection):
        query = sql.SQL("SELECT name FROM {} WHERE id = %s LIMIT 1").format(
            sql.Identifier(table)
        )
        with connection.cursor() as cursor:
            cursor.execute(query, [lookup_id])
            found = cursor.fetchone()
        if found is None:
            return None
        return found[0]

    name = run_query(work)
    if name is None:
        raise InvalidInputError(f"{label} با شناسه {lookup_id} پیدا نشد")
    return name


def fetch_account_record(account_id: int):
    """یک حساب را با نام نوع می‌خواند یا None."""
    return fetch_one(
        _ACCOUNT_SELECT + " WHERE a.id = %s",
        [account_id],
        ACCOUNT_COLUMNS,
    )


def fetch_account_records(limit: int, offset: int, is_active=None) -> list:
    """فهرست حساب‌ها را با فیلتر اختیاری فعال بودن می‌خواند."""
    extra = ""
    params = []
    if is_active is not None:
        extra = " WHERE a.is_active = %s"
        params.append(is_active)
    params.extend([limit, offset])
    return fetch_many(
        _ACCOUNT_SELECT + extra + " ORDER BY a.id DESC LIMIT %s OFFSET %s",
        params,
        ACCOUNT_COLUMNS,
    )


def fetch_transaction_record(transaction_id: int):
    """یک تراکنش را با نام نوع و دسته می‌خواند یا None."""
    return fetch_one(
        _TRANSACTION_SELECT + " WHERE tx.id = %s",
        [transaction_id],
        TRANSACTION_COLUMNS,
    )


def fetch_transaction_records(
    limit: int,
    offset: int,
    account_id=None,
    project_id=None,
) -> list:
    """فهرست تراکنش‌ها را با فیلتر حساب یا پروژه می‌خواند."""
    clauses = []
    params = []
    if account_id is not None:
        clauses.append("tx.account_id = %s")
        params.append(account_id)
    if project_id is not None:
        clauses.append("tx.project_id = %s")
        params.append(project_id)
    extra = ""
    if clauses:
        extra = " WHERE " + " AND ".join(clauses)
    params.extend([limit, offset])
    return fetch_many(
        _TRANSACTION_SELECT
        + extra
        + " ORDER BY tx.transaction_date DESC, tx.id DESC LIMIT %s OFFSET %s",
        params,
        TRANSACTION_COLUMNS,
    )


def fetch_category_record(category_id: int):
    """یک دسته را می‌خواند یا None."""
    return fetch_one(
        """
        SELECT id, name, description
        FROM financial_categories
        WHERE id = %s
        """,
        [category_id],
        CATEGORY_COLUMNS,
    )


def sum_account_transactions_on(connection, account_id: int):
    """جمع مبلغ تراکنش‌های یک حساب را روی اتصال باز برمی‌گرداند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM financial_transactions
            WHERE account_id = %s
            """,
            [account_id],
        )
        row = cursor.fetchone()
    return row[0]


def refresh_account_balance_on(connection, account_id: int):
    """ماندهٔ کمکی را از جمع تراکنش‌ها روی اتصال باز می‌نویسد."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE financial_accounts
            SET balance = (
                SELECT COALESCE(SUM(amount), 0)
                FROM financial_transactions
                WHERE account_id = %s
            )
            WHERE id = %s
            RETURNING balance
            """,
            [account_id, account_id],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return row[0]


def insert_account_on(connection, fields: dict) -> int:
    """یک حساب با ماندهٔ صفر درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO financial_accounts (name, account_type_id, balance, is_active)
            VALUES (%(name)s, %(account_type_id)s, 0, %(is_active)s)
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def insert_transaction_on(connection, fields: dict) -> int:
    """تراکنش را درج می‌کند و ماندهٔ حساب را از جمع تراکنش‌ها می‌نویسد."""
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
                %(transaction_date)s
            )
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    transaction_id = int(row[0])
    refresh_account_balance_on(connection, fields["account_id"])
    return transaction_id


def insert_category_on(connection, fields: dict) -> int:
    """یک دستهٔ مالی درج می‌کند."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO financial_categories (name, description)
            VALUES (%(name)s, %(description)s)
            RETURNING id
            """,
            fields,
        )
        row = cursor.fetchone()
    return int(row[0])


def insert_account(fields: dict) -> int:
    """حساب را با run_query درج می‌کند."""

    def work(connection):
        return insert_account_on(connection, fields)

    return run_query(work)


def insert_transaction(fields: dict) -> int:
    """تراکنش و ماندهٔ مشتق را در یک تراکنش دیتابیس می‌نویسد."""

    def work(connection):
        return insert_transaction_on(connection, fields)

    return run_query(work)


def insert_category(fields: dict) -> int:
    """دسته را با run_query درج می‌کند."""

    def work(connection):
        return insert_category_on(connection, fields)

    return run_query(work, UNIQUE_MESSAGES)
