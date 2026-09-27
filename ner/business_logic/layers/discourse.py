"""لایه discourse: ژانر / نوع پیام.

جدول هدف: text_analysis_discourses. نیت اینجا نیست.
اگر قالب کاتالوگ پر نشود ولی کنش ساخت‌یافته باشد، نوع نو نگه داشته می‌شود.
"""

from typing import Any

from business_logic.config import (
    load_column_config,
    load_discourse_catalog,
    load_discourse_discovery,
)
from business_logic.layers.discovery import (
    attach_catalog_discovery,
    merge_discourse_hits,
    novel_discourses_from_payload,
)
from business_logic.layers.labeled import labeled_hits_from_payload, _pick_primary
from schemas.output import DiscourseHit

_SOURCE_KEY = "project_texts"


def discourses_from_payload(payload: Any, normalized: str) -> list[DiscourseHit]:
    """ژانرهای مجاز و در صورت لزوم نوع کشف‌شده را از پاسخ مدل برمی‌دارد."""
    catalog = load_discourse_catalog()
    discovery = load_discourse_discovery()
    max_hits = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("discourses") or {}).get(
            "max"
        )
        or 3
    )
    catalog_hits = labeled_hits_from_payload(
        payload,
        list_key="discourses",
        catalog=catalog,
        max_hits=max_hits,
        hit_cls=DiscourseHit,
        normalized=normalized,
    )
    attach_catalog_discovery(catalog_hits, catalog)
    novel_hits = novel_discourses_from_payload(payload, normalized, catalog, discovery)
    hits = merge_discourse_hits(
        catalog_hits,
        novel_hits,
        catalog,
        max_hits=max_hits,
        do_not_force_fit=bool(discovery.get("do_not_force_fit", True)),
    )
    priority = {item["code"]: int(item["priority"]) for item in catalog}
    for item in hits:
        priority.setdefault(item.code, 0)
    _pick_primary(hits, priority_of=lambda code: priority.get(code, 0))
    hits.sort(
        key=lambda item: (
            not item.is_primary,
            -priority.get(item.code, 0),
            -item.confidence,
        )
    )
    return hits
