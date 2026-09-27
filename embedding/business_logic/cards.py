"""کارت فارسی برای امبدینگ متن خام و فکت استخراج‌شده.

متن خام و استخراج قاطی نمی‌شوند. کد کاتالوگ در کارت نمی‌آید.
"""

from logging_module import logged_step

_ENTITY_TYPE_NAMES = {
    "PERSON": "فرد",
    "UNIT": "واحد",
    "ORG": "سازمان",
    "PLACE": "مکان",
    "OBJECT": "شیء",
    "PROJECT": "پروژه",
    "TASK": "وظیفه",
    "TIME": "زمان",
    "ROLE": "نقش",
}

_SOURCE_LABELS = {
    "meeting": "جلسه",
    "message": "پیام",
    "content": "متن",
}

_CHUNK_SIZE = 1200
_CHUNK_OVERLAP = 120
_KINDS = ("raw", "entity", "intent", "intent_slot")


def source_label(source_type: str) -> str:
    """نام فارسی نوع منبع را برمی‌گرداند."""
    return _SOURCE_LABELS.get(source_type, source_type)


def chunk_raw_text(text: str) -> list[str]:
    """متن بلند را به بندهای کوتاه برای امبدینگ می‌شکند."""
    body = " ".join(str(text or "").split())
    if not body:
        return []
    if len(body) <= _CHUNK_SIZE:
        return [body]
    chunks = []
    start = 0
    length = len(body)
    while start < length:
        end = min(start + _CHUNK_SIZE, length)
        if end < length:
            cut = body.rfind(" ", start, end)
            if cut > start + 200:
                end = cut
        piece = body[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - _CHUNK_OVERLAP, start + 1)
    return chunks


def raw_card(source_type: str, chunk: str) -> str:
    """کارت متن خام با پیشوند سبک نوع منبع."""
    label = source_label(source_type)
    return f"{label}. {chunk}".strip()


def entity_card(entity: dict) -> str:
    """کارت موجودیت canonical با شاهد."""
    type_name = _ENTITY_TYPE_NAMES.get(str(entity.get("type") or ""), entity.get("type") or "موجودیت")
    name = str(entity.get("canonical_name") or "").strip()
    evidence = str(entity.get("mention_text") or name).strip()
    return f"موجودیت: {type_name}. نام: {name}. شاهد: {evidence}".strip()


def _slot_bits(slots: dict) -> list[str]:
    bits = []
    for name, value in (slots or {}).items():
        key = str(name or "").strip()
        text = str(value or "").strip()
        if key and text:
            bits.append(f"{key}: {text}")
    return bits


def intent_card(intent: dict) -> str:
    """کارت نیت با شاهد و اجزای پرشده."""
    name = str(intent.get("name") or intent.get("code") or "").strip()
    evidence = str(intent.get("mention_text") or "").strip()
    parts = [f"نیت: {name}"]
    if evidence:
        parts.append(f"شاهد: {evidence}")
    parts.extend(_slot_bits(intent.get("slots") or {}))
    return ". ".join(parts)


def intent_slot_card(intent: dict, slot_name: str, slot_value: str) -> str:
    """کارت یک جزء نیت."""
    name = str(intent.get("name") or intent.get("code") or "").strip()
    evidence = str(intent.get("mention_text") or slot_value).strip()
    return (
        f"جزء نیت {name}. نقش: {slot_name}. مقدار: {slot_value}. شاهد: {evidence}"
    ).strip()


@logged_step("calculate")
def cards_for_analysis(source_type: str, raw_text: str, analysis: dict) -> list[dict]:
    """کارت‌های خام و فکت یک تحلیل را می‌سازد."""
    cards = []
    for index, chunk in enumerate(chunk_raw_text(raw_text)):
        cards.append(
            {
                "kind": "raw",
                "record_id": None,
                "chunk_index": index,
                "embedded_text": raw_card(source_type, chunk),
            }
        )
    seen_entities = set()
    mentions_by_entity = {}
    for mention in analysis.get("mentions") or []:
        entity_id = mention.get("entity_id")
        if entity_id is not None:
            mentions_by_entity.setdefault(entity_id, mention)
    for entity in analysis.get("entities") or []:
        key = (entity.get("type"), entity.get("normalized_name") or entity.get("canonical_name"))
        if key in seen_entities:
            continue
        seen_entities.add(key)
        mention = mentions_by_entity.get(entity.get("id")) or {}
        card_entity = {
            **entity,
            "mention_text": mention.get("mention_text") or entity.get("canonical_name"),
        }
        record_id = entity.get("id") or mention.get("id")
        cards.append(
            {
                "kind": "entity",
                "record_id": record_id,
                "chunk_index": 0,
                "embedded_text": entity_card(card_entity),
            }
        )
    for intent in analysis.get("intents") or []:
        cards.append(
            {
                "kind": "intent",
                "record_id": intent.get("id"),
                "chunk_index": 0,
                "embedded_text": intent_card(intent),
            }
        )
        for slot_index, (slot_name, slot_value) in enumerate(
            (intent.get("slots") or {}).items()
        ):
            name = str(slot_name or "").strip()
            value = str(slot_value or "").strip()
            if not name or not value:
                continue
            cards.append(
                {
                    "kind": "intent_slot",
                    "record_id": intent.get("id"),
                    "chunk_index": slot_index,
                    "embedded_text": intent_slot_card(intent, name, value),
                }
            )
    return [
        item
        for item in cards
        if item["kind"] in _KINDS and str(item.get("embedded_text") or "").strip()
    ]
