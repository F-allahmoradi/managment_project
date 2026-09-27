"""لایه rhetoric: صنعت بیان / لحن غیرصریح.

جدول هدف: text_analysis_rhetorics. نیت و ژانر اینجا نیست.
"""

from typing import Any

from business_logic.config import load_column_config, load_rhetoric_catalog
from business_logic.layers.labeled import labeled_hits_from_payload
from schemas.output import RhetoricHit

_SOURCE_KEY = "project_texts"


def rhetorics_from_payload(
    payload: Any, normalized: str
) -> tuple[list[RhetoricHit], str]:
    """صنعت‌های بیان مجاز و معنای مقصود را از پاسخ مدل برمی‌دارد."""
    max_hits = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("rhetorics") or {}).get(
            "max"
        )
        or 2
    )
    hits = labeled_hits_from_payload(
        payload,
        list_key="rhetorics",
        catalog=load_rhetoric_catalog(),
        max_hits=max_hits,
        hit_cls=RhetoricHit,
        normalized=normalized,
    )
    meaning = ""
    if isinstance(payload, dict):
        meaning = str(payload.get("intended_meaning") or "").strip()
    if not meaning:
        primary = next((item for item in hits if item.is_primary), None)
        if primary is not None:
            meaning = str((primary.slots or {}).get("مقصود") or "").strip()
    if meaning:
        for item in hits:
            if item.is_primary:
                item.intended_meaning = meaning
                break
    return hits, meaning
