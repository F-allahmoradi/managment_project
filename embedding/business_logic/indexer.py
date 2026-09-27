"""ایندکس برداری روی تحلیل ذخیره‌شده. منبع حقیقت جداول تحلیل است."""

from business_logic.cards import cards_for_analysis
from business_logic.config import load_llm_public
from business_logic.embed_client import embed_texts
from business_logic.repository import (
    delete_analysis_embeddings,
    fetch_pending_analysis_ids,
    fetch_source_body,
    insert_embedding_rows,
)
from errors.crud import EmptyTranscriptError, InvalidInputError
from logging_module import logged_step
from services.text_analysis import fetch_text_analysis


@logged_step("insert")
def index_analysis(analysis_id: int, actor_id: int, embed_fn=None) -> dict:
    """متن خام، موجودیت، نیت و اجزای نیت یک تحلیل را برداری می‌کند."""
    analysis = fetch_text_analysis(analysis_id, actor_id)
    try:
        raw_text = fetch_source_body(analysis["source_type"], analysis["source_id"])
    except EmptyTranscriptError as exc:
        raise InvalidInputError(str(exc)) from exc
    cards = cards_for_analysis(analysis["source_type"], raw_text, analysis)
    if not cards:
        raise InvalidInputError("برای این تحلیل متن یا فکتی برای امبدینگ نیست")
    encode = embed_fn or embed_texts
    vectors = encode([item["embedded_text"] for item in cards])
    if len(vectors) != len(cards):
        raise InvalidInputError("تعداد بردار با تعداد کارت یکی نیست")
    settings = load_llm_public()
    model = str(settings.get("embedding_model") or "text-embedding-3-small").strip()
    rows = []
    for card, vector in zip(cards, vectors):
        rows.append(
            {
                "analysis_id": analysis_id,
                "kind": card["kind"],
                "record_id": card.get("record_id"),
                "chunk_index": card.get("chunk_index") or 0,
                "embedded_text": card["embedded_text"],
                "model": model,
                "embedding": [float(value) for value in vector],
            }
        )
    delete_analysis_embeddings(analysis_id)
    insert_embedding_rows(rows)
    counts = {"raw": 0, "entity": 0, "intent": 0, "intent_slot": 0}
    for card in cards:
        counts[card["kind"]] = counts.get(card["kind"], 0) + 1
    return {
        "analysis_id": analysis_id,
        "source_type": analysis["source_type"],
        "source_id": analysis["source_id"],
        "model": model,
        "indexed_count": len(rows),
        "card_count": len(cards),
        "raw_count": counts["raw"],
        "entity_count": counts["entity"],
        "intent_count": counts["intent"],
        "intent_slot_count": counts["intent_slot"],
    }


@logged_step("insert")
def index_pending(actor_id: int, limit: int, embed_fn=None) -> dict:
    """تحلیل‌های بدون بردار همین مدل را ایندکس می‌کند."""
    settings = load_llm_public()
    model = str(settings.get("embedding_model") or "text-embedding-3-small").strip()
    ids = fetch_pending_analysis_ids(actor_id, model, limit)
    records = []
    for analysis_id in ids:
        records.append(index_analysis(analysis_id, actor_id, embed_fn=embed_fn))
    return {
        "model": model,
        "indexed_count": len(records),
        "records": records,
    }
