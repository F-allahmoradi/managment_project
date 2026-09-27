"""بازیابی موارد مشابه از بردار خام و فکت. آمار عملیاتی اینجا نیست."""

from business_logic.config import load_llm_public
from business_logic.embed_client import embed_texts
from business_logic.repository import search_visible_embeddings
from business_logic.similarity import rank_hits
from logging_module import logged_step

_ALL_KINDS = ["raw", "entity", "intent", "intent_slot"]


@logged_step("fetch")
def search_similar(
    actor_id: int,
    query: str,
    kinds=None,
    source_type=None,
    limit: int = 8,
    embed_fn=None,
) -> dict:
    """نزدیک‌ترین متن خام و فکت‌ها را برای سؤال برمی‌گرداند."""
    settings = load_llm_public()
    model = str(settings.get("embedding_model") or "text-embedding-3-small").strip()
    selected = list(kinds or _ALL_KINDS)
    encode = embed_fn or embed_texts
    query_vector = encode([query])[0]
    rows = search_visible_embeddings(
        actor_id,
        model,
        query_vector,
        selected,
        source_type=source_type,
        limit=limit,
    )
    records = rank_hits(query_vector, rows, limit)
    return {
        "query": query,
        "model": model,
        "kinds": selected,
        "source_type": source_type,
        "hit_count": len(records),
        "records": records,
    }
