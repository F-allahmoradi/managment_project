"""خواندن متن منبع و ذخیره/خواندن بردار بازیابی.

INSERT تحلیل متن اینجا نیست؛ فقط text_embeddings نوشته می‌شود.
"""

from business_logic.config import EMBEDDING_DIMENSIONS
from errors.crud import EmptyTranscriptError, InvalidInputError
from logging_module import logged_step
from repository.columns import unique_messages_for
from repository.db import fetch_many, fetch_one, run_query

_SOURCE_BODY_COLUMNS = ("text",)
_PENDING_COLUMNS = ("id",)
_EMBED_KIND_COUNT_COLUMNS = ("analysis_id", "kind", "card_count")
_SEARCH_COLUMNS = (
    "analysis_id",
    "kind",
    "record_id",
    "chunk_index",
    "embedded_text",
    "source_type",
    "source_id",
    "score",
)
_CANDIDATE_MULTIPLIER = 8
_CANDIDATE_FLOOR = 48


def as_pgvector(values) -> str:
    """لیست عدد را به نویسهٔ پذیرفتهٔ نوع vector تبدیل می‌کند."""
    if not isinstance(values, (list, tuple)):
        raise InvalidInputError("بردار امبدینگ نامعتبر است")
    if len(values) != EMBEDDING_DIMENSIONS:
        raise InvalidInputError(f"طول بردار باید {EMBEDDING_DIMENSIONS} باشد")
    try:
        return "[" + ",".join(str(float(item)) for item in values) + "]"
    except (TypeError, ValueError) as exc:
        raise InvalidInputError("بردار امبدینگ نامعتبر است") from exc


@logged_step("fetch")
def fetch_source_body(source_type: str, source_id: int) -> str:
    """متن خام منبع تحلیل را بدون بررسی دسترسی دوباره می‌خواند."""
    if source_type == "content":
        row = fetch_one(
            "SELECT text_body AS text FROM contents WHERE id = %s",
            [source_id],
            _SOURCE_BODY_COLUMNS,
        )
    elif source_type == "message":
        row = fetch_one(
            """
            SELECT COALESCE(NULLIF(BTRIM(m.text), ''), c.text_body) AS text
            FROM messages m
            LEFT JOIN contents c ON c.id = m.content_id
            WHERE m.id = %s
            """,
            [source_id],
            _SOURCE_BODY_COLUMNS,
        )
    elif source_type == "meeting":
        row = fetch_one(
            """
            SELECT c.text_body AS text
            FROM meetings mt
            LEFT JOIN contents c ON c.id = mt.content_id
            WHERE mt.id = %s
            """,
            [source_id],
            _SOURCE_BODY_COLUMNS,
        )
    else:
        raise InvalidInputError("source_type باید meeting یا message یا content باشد")
    body = (row or {}).get("text")
    if body is None or not str(body).strip():
        raise EmptyTranscriptError("متن منبع خالی است")
    return str(body).strip()


def delete_analysis_embeddings(analysis_id: int) -> None:
    """بردارهای قبلی همان تحلیل را پاک می‌کند تا نسخهٔ زنده یکی بماند."""

    def work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM text_embeddings WHERE analysis_id = %s",
                [analysis_id],
            )

    run_query(work)


def insert_embedding_rows(rows: list[dict]) -> int:
    """کارت‌های برداری را در text_embeddings می‌نویسد."""
    if not rows:
        return 0
    prepared = []
    for row in rows:
        prepared.append({**row, "embedding": as_pgvector(row.get("embedding"))})

    def work(connection):
        count = 0
        with connection.cursor() as cursor:
            for row in prepared:
                cursor.execute(
                    """
                    INSERT INTO text_embeddings
                        (analysis_id, kind, record_id, chunk_index,
                         embedded_text, model, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                    """,
                    [
                        row["analysis_id"],
                        row["kind"],
                        row.get("record_id"),
                        row.get("chunk_index") or 0,
                        row["embedded_text"],
                        row["model"],
                        row["embedding"],
                    ],
                )
                count += 1
        return count

    return run_query(work, unique_messages_for("text_embeddings"))


def fetch_embedding_summaries(analysis_ids: list[int], model: str) -> list[dict]:
    """شمار کارت بردار هر تحلیل را برای همین مدل جمع می‌کند."""
    if not analysis_ids:
        return []
    rows = fetch_many(
        """
        SELECT analysis_id, kind, COUNT(*) AS card_count
        FROM text_embeddings
        WHERE model = %s AND analysis_id = ANY(%s)
        GROUP BY analysis_id, kind
        """,
        [model, list(analysis_ids)],
        _EMBED_KIND_COUNT_COLUMNS,
    )
    grouped = {}
    for row in rows:
        item = grouped.setdefault(
            int(row["analysis_id"]),
            {
                "analysis_id": int(row["analysis_id"]),
                "card_count": 0,
                "raw_count": 0,
                "entity_count": 0,
                "intent_count": 0,
                "intent_slot_count": 0,
            },
        )
        count = int(row["card_count"] or 0)
        item["card_count"] += count
        key = f"{row['kind']}_count"
        if key in item:
            item[key] = count
    return list(grouped.values())


def fetch_pending_analysis_ids(actor_id: int, model: str, limit: int) -> list[int]:
    """تحلیل‌های قابل‌مشاهدهٔ بازیگر که بردار این مدل را ندارند."""
    rows = fetch_visible_embeddings_query_pending(actor_id, model, limit)
    return [int(row["id"]) for row in rows]


def fetch_visible_embeddings_query_pending(actor_id: int, model: str, limit: int) -> list:
    """شناسه تحلیل‌های بدون بردار همین مدل را می‌خواند."""
    sql, params = _visible_analysis_sql(actor_id)
    return fetch_many(
        f"""
        SELECT a.id
        FROM text_analyses a
        JOIN analysis_source_types st ON st.id = a.source_type_id
        LEFT JOIN contents c ON st.code = 'content' AND c.id = a.source_id
        LEFT JOIN messages m ON st.code = 'message' AND m.id = a.source_id
        LEFT JOIN meetings mt ON st.code = 'meeting' AND mt.id = a.source_id
        WHERE {sql}
          AND NOT EXISTS (
                SELECT 1 FROM text_embeddings e
                WHERE e.analysis_id = a.id AND e.model = %s
          )
        ORDER BY a.id DESC
        LIMIT %s
        """,
        [*params, model, limit],
        _PENDING_COLUMNS,
    )


def search_visible_embeddings(
    actor_id: int,
    model: str,
    query_vector: list[float],
    kinds: list[str],
    source_type=None,
    limit: int = 8,
) -> list:
    """نزدیک‌ترین بردارهای قابل‌مشاهده را با HNSW کسینوس می‌خواند."""
    access_sql, params = _visible_analysis_sql(actor_id)
    filters = ["e.model = %s", access_sql]
    values = [model, *params]
    if kinds:
        filters.append("e.kind = ANY(%s)")
        values.append(kinds)
    if source_type:
        filters.append("st.code = %s")
        values.append(source_type)
    where_sql = " AND ".join(filters)
    query_literal = as_pgvector(query_vector)
    candidate_limit = max(int(limit) * _CANDIDATE_MULTIPLIER, _CANDIDATE_FLOOR)
    return fetch_many(
        f"""
        SELECT e.analysis_id, e.kind, e.record_id, e.chunk_index,
               e.embedded_text, st.code AS source_type, a.source_id,
               1 - (e.embedding <=> %s::vector) AS score
        FROM text_embeddings e
        JOIN text_analyses a ON a.id = e.analysis_id
        JOIN analysis_source_types st ON st.id = a.source_type_id
        LEFT JOIN contents c ON st.code = 'content' AND c.id = a.source_id
        LEFT JOIN messages m ON st.code = 'message' AND m.id = a.source_id
        LEFT JOIN meetings mt ON st.code = 'meeting' AND mt.id = a.source_id
        WHERE {where_sql}
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
        """,
        [query_literal, *values, query_literal, candidate_limit],
        _SEARCH_COLUMNS,
    )


def _visible_analysis_sql(actor_id: int) -> tuple[str, list]:
    """شرط دسترسی منبع را برای JOINهای تحلیل برمی‌گرداند."""
    return (
        """(
            (st.code = 'content' AND c.created_by_user_id = %s)
            OR (
                st.code = 'message' AND EXISTS (
                    SELECT 1 FROM chat_members cm
                    WHERE cm.chat_id = m.chat_id AND cm.user_id = %s
                )
            )
            OR (
                st.code = 'meeting' AND (
                    mt.manager_user_id = %s
                    OR EXISTS (
                        SELECT 1 FROM meeting_participants mp
                        WHERE mp.meeting_id = mt.id AND mp.user_id = %s
                    )
                    OR (
                        mt.visibility = 'PROJECT'
                        AND mt.project_id IS NOT NULL
                        AND EXISTS (
                            SELECT 1 FROM project_members pm
                            WHERE pm.project_id = mt.project_id
                              AND pm.user_id = %s
                              AND pm.is_active = true
                        )
                    )
                )
            )
        )""",
        [actor_id, actor_id, actor_id, actor_id, actor_id],
    )
