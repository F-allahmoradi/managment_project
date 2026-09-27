"""لایه intent: نیت گوینده / مسیر رسیدگی.

جدول هدف: text_analysis_intents. ژانر متن اینجا نیست.
"""

from typing import Any

from business_logic.config import load_column_config, load_intent_catalog
from business_logic.layers.labeled import labeled_hits_from_payload
from schemas.output import IntentHit

_SOURCE_KEY = "project_texts"


def intents_from_payload(payload: Any, normalized: str) -> list[IntentHit]:
    """نیت‌های مجاز را از پاسخ مدل برمی‌دارد."""
    max_hits = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("intents") or {}).get(
            "max"
        )
        or 2
    )
    return labeled_hits_from_payload(
        payload,
        list_key="intents",
        catalog=load_intent_catalog(),
        max_hits=max_hits,
        hit_cls=IntentHit,
        normalized=normalized,
    )
