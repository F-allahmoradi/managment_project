"""شباهت کسینوس و ادغام hitهای یک منبع."""

from logging_module import logged_step


def _as_vector(value) -> list[float]:
    """خروجی PostgreSQL یا لیست پایتون را به بردار عدد تبدیل می‌کند."""
    if value is None:
        return []
    if isinstance(value, str):
        body = value.strip().lstrip("{").rstrip("}")
        if not body:
            return []
        return [float(part) for part in body.split(",") if part.strip()]
    return [float(item) for item in value]


def cosine(left, right) -> float:
    """شباهت کسینوس دو بردار هم‌طول."""
    left_vec = _as_vector(left)
    right_vec = _as_vector(right)
    if not left_vec or not right_vec or len(left_vec) != len(right_vec):
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for x, y in zip(left_vec, right_vec):
        dot += x * y
        left_norm += x * x
        right_norm += y * y
    if left_norm <= 0 or right_norm <= 0:
        return 0.0
    return dot / ((left_norm ** 0.5) * (right_norm ** 0.5))


@logged_step("calculate")
def rank_hits(query_vector: list[float], rows: list[dict], limit: int) -> list[dict]:
    """hitها را گروه منبع می‌کند و با بیشترین امتیاز مرتب می‌کند."""
    scored = []
    for row in rows:
        if row.get("score") is not None:
            score = float(row["score"])
        else:
            score = cosine(query_vector, row.get("embedding") or [])
        if score <= 0:
            continue
        scored.append(
            {
                "analysis_id": row["analysis_id"],
                "source_type": row["source_type"],
                "source_id": row["source_id"],
                "kind": row["kind"],
                "record_id": row.get("record_id"),
                "chunk_index": row.get("chunk_index") or 0,
                "text": row.get("embedded_text") or row.get("text") or "",
                "score": round(float(score), 4),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    grouped = []
    seen = {}
    for hit in scored:
        key = hit["analysis_id"]
        if key not in seen:
            record = {
                "analysis_id": hit["analysis_id"],
                "source_type": hit["source_type"],
                "source_id": hit["source_id"],
                "score": hit["score"],
                "kinds": [],
                "hits": [],
            }
            seen[key] = record
            grouped.append(record)
        record = seen[key]
        if len(record["hits"]) >= 4:
            continue
        record["hits"].append(
            {
                "kind": hit["kind"],
                "score": hit["score"],
                "text": hit["text"],
                "record_id": hit["record_id"],
                "chunk_index": hit["chunk_index"],
            }
        )
        if hit["kind"] not in record["kinds"]:
            record["kinds"].append(hit["kind"])
        if hit["score"] > record["score"]:
            record["score"] = hit["score"]
    grouped.sort(key=lambda item: item["score"], reverse=True)
    return grouped[:limit]
