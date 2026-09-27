"""سرویس ذخیره خروجی NER در جداول تحلیل متن.

NER فقط استخراج می‌کند. اینجا ردیف‌ها با وضعیت پیشنهادی درج می‌شوند.
"""

from decimal import Decimal, ROUND_HALF_UP

from auth.gate import require_chat_member
from errors.crud import (
    ContentNotFoundError,
    InvalidInputError,
    MessageNotFoundError,
    PermissionDeniedError,
    TextAnalysisNotFoundError,
)
from logging_module import logged_step
from repository import (
    fetch_first,
    fetch_first_on,
    fetch_meeting_participant_record,
    fetch_source_access_record,
    fetch_text_analyses_for_actor_records,
    fetch_text_analysis_emotions_records,
    fetch_text_analysis_entities_records,
    fetch_text_analysis_discourses_records,
    fetch_text_analysis_intents_records,
    fetch_text_analysis_intent_slots_records,
    fetch_text_analysis_discourse_slots_records,
    fetch_text_analysis_rhetorics_records,
    fetch_text_analysis_rhetoric_slots_records,
    fetch_text_analysis_facts_records,
    fetch_text_analysis_quotes_records,
    fetch_text_analysis_mentions_records,
    fetch_text_analysis_keywords_records,
    fetch_text_analysis_record,
    fetch_text_analysis_sentiment_record,
    fetch_text_analysis_topics_records,
    insert_row_on,
    run_query,
)
from services.audit_log import ACTION_CREATE, record_audit_on
from services.project import fetch_active_membership

_CANDIDATE_STATUS = "candidate"
_TEXT_KIND = "TEXT"
_CONFIDENCE_QUANT = Decimal("0.0001")
_VALUE_QUANT = Decimal("0.0001")


def _not_found_message(analysis_id: int) -> str:
    return f"تحلیل متن با شناسه {analysis_id} پیدا نشد"


def _as_confidence(value) -> Decimal:
    number = Decimal(str(value)).quantize(_CONFIDENCE_QUANT, rounding=ROUND_HALF_UP)
    if number < 0 or number > 1:
        raise InvalidInputError("اطمینان باید بین ۰ و ۱ باشد")
    return number


def _as_mention_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_value(value):
    if value is None or value == "":
        return None
    return Decimal(str(value)).quantize(_VALUE_QUANT, rounding=ROUND_HALF_UP)


def _as_text_list(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, str):
        text = raw.strip()
        return [text] if text else []
    items = []
    for value in raw:
        text = str(value or "").strip()
        if text:
            items.append(text[:300])
    return items


def _fact_offsets(item: dict):
    start = item.get("start_offset")
    end = item.get("end_offset")
    if not isinstance(start, int) or start < 0:
        return None, None
    if not isinstance(end, int) or end <= start:
        return None, None
    return start, end


def _lookup_fact(item: dict) -> dict:
    """کدهای کاتالوگ یک فکت را به ردیف lookup می‌برد."""
    kind = _lookup_by_code("fact_kinds", item["kind"], "نوع فکت")
    role = _lookup_by_code(
        "fact_quantity_roles",
        item.get("role") or "none",
        "نقش مقدار",
    )
    grounding = _lookup_by_code("fact_groundings", item["grounding"], "صراحت فکت")
    unit = None
    if item.get("unit"):
        unit = _lookup_by_code("fact_units", item["unit"], "واحد مقدار")
    derivation = None
    if item.get("derivation"):
        derivation = _lookup_by_code("fact_derivations", item["derivation"], "حساب فکت")
    return {
        "kind": kind,
        "role": role,
        "grounding": grounding,
        "unit": unit,
        "derivation": derivation,
    }


def _insert_facts_on(connection, analysis_id: int, facts: list) -> int:
    """فکت‌ها را روی اتصال باز می‌نویسد؛ کد تکراری در همین فهرست را رد می‌کند."""
    seen_codes = set()
    written = 0
    for item in facts or []:
        code = str(item.get("fact_id") or "").strip()[:40]
        if code and code in seen_codes:
            continue
        if code:
            seen_codes.add(code)
        lookups = _lookup_fact(item)
        start, end = _fact_offsets(item)
        row = {
            "analysis_id": analysis_id,
            "fact_code": code,
            "kind_id": lookups["kind"]["id"],
            "name": str(item.get("name") or "").strip()[:200],
            "value": _as_value(item.get("value")),
            "role_id": lookups["role"]["id"],
            "grounding_id": lookups["grounding"]["id"],
            "effect": _as_mention_text(item.get("effect"))[:300],
            "previous": _as_mention_text(item.get("previous"))[:300],
            "current": _as_mention_text(item.get("current"))[:300],
            "mention_text": _as_mention_text(item.get("mention_text")),
            "evidence_texts": _as_text_list(item.get("evidence_texts")),
            "source_ids": _as_text_list(item.get("source_ids")),
            "confidence": _as_confidence(item.get("confidence") or 1),
        }
        if lookups["unit"] is not None:
            row["unit_id"] = lookups["unit"]["id"]
        if lookups["derivation"] is not None:
            row["derivation_id"] = lookups["derivation"]["id"]
        if start is not None:
            row["start_offset"] = start
            row["end_offset"] = end
        insert_row_on(connection, "text_analysis_facts", row)
        written += 1
    return written


def _normalize_keyword_phrase(value: str) -> str:
    return " ".join(str(value or "").split())[:200]


def _keyword_offsets(item: dict):
    start = item.get("start_offset")
    end = item.get("end_offset")
    if not isinstance(start, int) or start < 0:
        return None, None
    if not isinstance(end, int) or end <= start:
        return None, None
    return start, end


def _lookup_or_create_keyword(connection, phrase: str) -> dict:
    """عبارت canonical را می‌خواند یا می‌سازد."""
    normalized = _normalize_keyword_phrase(phrase)
    existing = fetch_first_on(connection, "keywords", {"normalized_phrase": normalized})
    if existing is not None:
        return existing
    insert_row_on(
        connection,
        "keywords",
        {"phrase": normalized, "normalized_phrase": normalized},
    )
    created = fetch_first_on(connection, "keywords", {"normalized_phrase": normalized})
    if created is None:
        raise InvalidInputError(f"عبارت کلیدی «{normalized}» ثبت نشد")
    return created


def _insert_keywords_on(connection, analysis_id: int, keywords: list, lineage: dict) -> int:
    """ذکر کلمهٔ کلیدی را با ربط به متن خام و پروژه می‌نویسد."""
    seen = set()
    written = 0
    for item in keywords or []:
        phrase = _normalize_keyword_phrase(item.get("phrase") or "")
        if not phrase:
            continue
        start, end = _keyword_offsets(item)
        key = (phrase, start, end)
        if key in seen:
            continue
        seen.add(key)
        keyword = _lookup_or_create_keyword(connection, phrase)
        row = {
            "keyword_id": keyword["id"],
            "analysis_id": analysis_id,
            "source_type_id": lineage["source_type_id"],
            "source_id": lineage["source_id"],
            "created_by_user_id": lineage["created_by_user_id"],
            "mention_text": _as_mention_text(item.get("mention_text") or phrase)[:300],
            "confidence": _as_confidence(item.get("confidence") or 1),
        }
        if lineage.get("project_id") is not None:
            row["project_id"] = lineage["project_id"]
        if start is not None:
            row["start_offset"] = start
            row["end_offset"] = end
        insert_row_on(connection, "keyword_mentions", row)
        written += 1
    return written


def _quote_offsets(item: dict):
    start = item.get("start_offset")
    end = item.get("end_offset")
    if not isinstance(start, int) or start < 0:
        return None, None
    if not isinstance(end, int) or end <= start:
        return None, None
    return start, end


def _lookup_quote(item: dict) -> dict:
    """کد شیوه نقل را به ردیف lookup می‌برد."""
    return _lookup_by_code("quote_modes", item["mode"], "شیوه نقل")


def _insert_quotes_on(connection, analysis_id: int, quotes: list) -> int:
    """نقل‌قول‌ها را روی اتصال باز می‌نویسد؛ گوینده و متن تکراری را رد می‌کند."""
    seen = set()
    written = 0
    for item in quotes or []:
        mode = _lookup_quote(item)
        speaker = str(item.get("attributed_to") or "").strip()[:200]
        quoted = str(item.get("quoted_text") or "").strip()
        key = (mode["id"], speaker, quoted)
        if not speaker or not quoted or key in seen:
            continue
        seen.add(key)
        start, end = _quote_offsets(item)
        row = {
            "analysis_id": analysis_id,
            "mode_id": mode["id"],
            "attributed_to": speaker,
            "quoted_text": quoted,
            "mention_text": _as_mention_text(item.get("mention_text")),
            "confidence": _as_confidence(item.get("confidence") or 1),
        }
        if start is not None:
            row["start_offset"] = start
            row["end_offset"] = end
        insert_row_on(connection, "text_analysis_quotes", row)
        written += 1
    return written


def _format_discourse_description(item: dict) -> str:
    """تعریف نوع نو را با نقش‌هایش برای ستون description می‌سازد."""
    parts = []
    definition = str(item.get("definition") or "").strip()
    if definition:
        parts.append(definition)
    required = []
    for slot in item.get("required_slots") or []:
        name = str(slot.get("name") if isinstance(slot, dict) else slot or "").strip()
        if name:
            required.append(name)
    optional = []
    for slot in item.get("optional_slots") or []:
        name = str(slot.get("name") if isinstance(slot, dict) else slot or "").strip()
        if name:
            optional.append(name)
    if required:
        parts.append("نقش اجباری: " + "؛ ".join(required))
    if optional:
        parts.append("نقش اختیاری: " + "؛ ".join(optional))
    return "\n".join(parts)


def _unique_discourse_name(connection, name: str, code: str) -> str:
    """نام تکراری نوع دیگر را با کد متمایز می‌کند؛ ردیف قبلی را عوض نمی‌کند."""
    base = (name or code).strip()[:100] or code[:100]
    existing = fetch_first_on(connection, "discourse_types", {"name": base})
    if existing is None or existing.get("code") == code:
        return base
    tagged = f"{base[:80]} ({code})"[:100]
    collision = fetch_first_on(connection, "discourse_types", {"name": tagged})
    if collision is None or collision.get("code") == code:
        return tagged
    return f"{code}"[:100]


def _lookup_or_create_discourse_type(connection, item: dict) -> dict:
    """ژانر کاتالوگ را می‌خواند یا نوع کشف‌شده را با ساختار خودش می‌سازد."""
    code = str(item.get("code") or "").strip()
    row = fetch_first_on(connection, "discourse_types", {"code": code})
    if row is not None:
        if row.get("is_active") is False:
            raise InvalidInputError(f"ژانر متن «{code}» غیرفعال است")
        return row
    if not item.get("discovered"):
        raise InvalidInputError(f"ژانر متن «{code}» پیدا نشد")
    name = str(item.get("name") or code).strip() or code
    insert_row_on(
        connection,
        "discourse_types",
        {
            "code": code[:40],
            "name": _unique_discourse_name(connection, name, code),
            "description": _format_discourse_description(item) or None,
            "is_active": True,
            "is_discovered": True,
        },
    )
    created = fetch_first_on(connection, "discourse_types", {"code": code})
    if created is None:
        raise InvalidInputError(f"ژانر متن «{code}» ثبت نشد")
    return created


def _lookup_or_create_topic(connection, item: dict) -> dict:
    """موضوع کاتالوگ را می‌خواند یا موضوع کشف‌شده را می‌سازد."""
    code = str(item.get("code") or "").strip()
    row = fetch_first_on(connection, "topics", {"code": code})
    if row is not None:
        if row.get("is_active") is False:
            raise InvalidInputError(f"موضوع «{code}» غیرفعال است")
        return row
    if not item.get("discovered"):
        raise InvalidInputError(f"موضوع «{code}» پیدا نشد")
    name = str(item.get("name") or code).strip() or code
    insert_row_on(
        connection,
        "topics",
        {
            "code": code[:80],
            "name": name[:100],
            "level": 1,
            "is_active": True,
        },
    )
    created = fetch_first_on(connection, "topics", {"code": code})
    if created is None:
        raise InvalidInputError(f"موضوع «{code}» ثبت نشد")
    return created


def _lookup_by_code(entity_key: str, code: str, label: str) -> dict:
    row = fetch_first(entity_key, {"code": code})
    if row is None:
        raise InvalidInputError(f"{label} «{code}» پیدا نشد")
    if row.get("is_active") is False:
        raise InvalidInputError(f"{label} «{code}» غیرفعال است")
    return row


def _require_source_access(actor_id: int, source_type: str, source_id: int) -> dict:
    """اگر بازیگر به منبع عملیاتی دسترسی نداشته باشد خطا می‌دهد."""
    source = fetch_source_access_record(source_type, source_id)
    if source is None:
        if source_type == "message":
            raise MessageNotFoundError(f"پیام با شناسه {source_id} پیدا نشد")
        if source_type == "content":
            raise ContentNotFoundError(f"محتوا با شناسه {source_id} پیدا نشد")
        raise InvalidInputError(f"منبع {source_type} با شناسه {source_id} پیدا نشد")
    if source_type == "message":
        require_chat_member(actor_id, source["chat_id"])
        return source
    if source_type == "content":
        if source["created_by_user_id"] != actor_id:
            raise PermissionDeniedError("به این محتوا دسترسی ندارید")
        return source
    if source["manager_user_id"] == actor_id:
        return source
    if source.get("visibility") == "PROJECT" and source.get("project_id") is not None:
        if fetch_active_membership(source["project_id"], actor_id) is not None:
            return source
    if fetch_meeting_participant_record(source_id, actor_id) is not None:
        return source
    raise PermissionDeniedError("به این جلسه دسترسی ندارید")


def _payload_from_analysis(analysis: dict) -> dict:
    analysis_id = analysis["id"]
    mentions = fetch_text_analysis_mentions_records(analysis_id)
    keywords = fetch_text_analysis_keywords_records(analysis_id)
    topics = fetch_text_analysis_topics_records(analysis_id)
    sentiment = fetch_text_analysis_sentiment_record(analysis_id)
    emotions = fetch_text_analysis_emotions_records(analysis_id)
    discourses = fetch_text_analysis_discourses_records(analysis_id)
    intents = fetch_text_analysis_intents_records(analysis_id)
    rhetorics = fetch_text_analysis_rhetorics_records(analysis_id)
    slot_rows = fetch_text_analysis_intent_slots_records(analysis_id)
    discourse_slot_rows = fetch_text_analysis_discourse_slots_records(analysis_id)
    rhetoric_slot_rows = fetch_text_analysis_rhetoric_slots_records(analysis_id)
    slots_by_intent = {}
    for slot in slot_rows:
        slots_by_intent.setdefault(slot["analysis_intent_id"], {})[slot["slot_name"]] = (
            slot["slot_value"]
        )
    for intent in intents:
        intent["slots"] = slots_by_intent.get(intent["id"], {})
    slots_by_discourse = {}
    for slot in discourse_slot_rows:
        slots_by_discourse.setdefault(slot["analysis_discourse_id"], {})[slot["slot_name"]] = (
            slot["slot_value"]
        )
    for discourse in discourses:
        discourse["slots"] = slots_by_discourse.get(discourse["id"], {})
    slots_by_rhetoric = {}
    for slot in rhetoric_slot_rows:
        slots_by_rhetoric.setdefault(slot["analysis_rhetoric_id"], {})[slot["slot_name"]] = (
            slot["slot_value"]
        )
    document_meaning = ""
    for rhetoric in rhetorics:
        rhetoric["slots"] = slots_by_rhetoric.get(rhetoric["id"], {})
        if rhetoric.get("is_primary") and rhetoric.get("intended_meaning"):
            document_meaning = rhetoric["intended_meaning"]
    if not document_meaning:
        for rhetoric in rhetorics:
            if rhetoric.get("intended_meaning"):
                document_meaning = rhetoric["intended_meaning"]
                break
    entities = fetch_text_analysis_entities_records(analysis_id)
    facts = fetch_text_analysis_facts_records(analysis_id)
    quotes = fetch_text_analysis_quotes_records(analysis_id)
    return {
        **analysis,
        "mentions": mentions,
        "mention_count": len(mentions),
        "keywords": keywords,
        "keyword_count": len(keywords),
        "entities": entities,
        "canonical_count": len(entities),
        "topics": topics,
        "topic_count": len(topics),
        "sentiment": sentiment,
        "emotions": emotions,
        "emotion_count": len(emotions),
        "discourses": discourses,
        "discourse_count": len(discourses),
        "intents": intents,
        "intent_count": len(intents),
        "rhetorics": rhetorics,
        "rhetoric_count": len(rhetorics),
        "facts": facts,
        "fact_count": len(facts),
        "quotes": quotes,
        "quote_count": len(quotes),
        "intended_meaning": document_meaning,
        "entity_status": _CANDIDATE_STATUS,
    }


def require_text_analysis_access(analysis_id: int, actor_id: int) -> dict:
    """وجود تحلیل و دسترسی به منبع را بررسی می‌کند؛ ذکرها را نمی‌خواند."""
    row = fetch_text_analysis_record(analysis_id)
    if row is None:
        raise TextAnalysisNotFoundError(_not_found_message(analysis_id))
    _require_source_access(actor_id, row["source_type"], row["source_id"])
    return row


def fetch_text_analysis(analysis_id: int, actor_id: int) -> dict:
    """یک تحلیل را با ذکرها می‌خواند؛ فقط اگر به منبع دسترسی باشد."""
    row = fetch_text_analysis_record(analysis_id)
    if row is None:
        raise TextAnalysisNotFoundError(_not_found_message(analysis_id))
    _require_source_access(actor_id, row["source_type"], row["source_id"])
    return _payload_from_analysis(row)


def fetch_text_analyses_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    source_type=None,
    source_id=None,
) -> list:
    """تحلیل‌های ساخته‌شده توسط کاربر جاری را می‌خواند."""
    if source_type is not None and source_id is not None:
        _require_source_access(user_id, source_type, source_id)
    return fetch_text_analyses_for_actor_records(
        user_id,
        limit,
        offset,
        source_type=source_type,
        source_id=source_id,
    )


def insert_text_analysis(fields: dict, created_by: int) -> dict:
    """خروجی استخراج را با وضعیت پیشنهادی در جداول تحلیل می‌نویسد."""
    source_type = fields["source_type"]
    source_id = fields.get("source_id")
    source_type_row = _lookup_by_code(
        "analysis_source_types",
        source_type,
        "نوع منبع تحلیل",
    )
    candidate = _lookup_by_code("entity_statuses", _CANDIDATE_STATUS, "وضعیت موجودیت")
    type_rows = {
        mention["type"]: _lookup_by_code("entity_types", mention["type"], "نوع موجودیت")
        for mention in fields.get("mentions") or []
    }
    intent_rows = {
        item["code"]: _lookup_by_code("intents", item["code"], "نیت")
        for item in fields.get("intents") or []
    }
    rhetoric_rows = {
        item["code"]: _lookup_by_code("rhetoric_types", item["code"], "صنعت بیان")
        for item in fields.get("rhetorics") or []
    }
    for item in fields.get("facts") or []:
        _lookup_fact(item)
    for item in fields.get("quotes") or []:
        _lookup_quote(item)
    sentiment = fields.get("sentiment")
    polarity_row = None
    sentiment_intensity = None
    if sentiment is not None:
        polarity_row = _lookup_by_code("polarities", sentiment["polarity"], "قطبیت")
        sentiment_intensity = _lookup_by_code(
            "intensity_levels",
            sentiment["intensity"],
            "شدت احساس",
        )
    emotion_rows = []
    for item in fields.get("emotions") or []:
        emotion_rows.append(
            (
                _lookup_by_code("emotions", item["emotion"], "هیجان"),
                _lookup_by_code("intensity_levels", item["intensity"], "شدت احساس"),
            )
        )
    text_kind = None
    if source_type == "content" and source_id is None:
        text_kind = fetch_first("content_kinds", {"code": _TEXT_KIND})
        if text_kind is None:
            raise InvalidInputError("نوع محتوای TEXT پیدا نشد")

    source = None
    if source_id is not None:
        source = _require_source_access(created_by, source_type, source_id)

    def work(connection):
        resolved_source_id = source_id
        if source_type == "content" and resolved_source_id is None:
            resolved_source_id = insert_row_on(
                connection,
                "contents",
                {
                    "content_kind_id": text_kind["id"],
                    "text_body": fields["text"],
                    "created_by_user_id": created_by,
                },
            )
        project_id = source.get("project_id") if source else None
        source_user_id = (
            source.get("created_by_user_id") if source else created_by
        ) or created_by
        analysis_row = {
            "source_type_id": source_type_row["id"],
            "source_id": resolved_source_id,
            "model": fields["model"],
            "created_by_user_id": created_by,
        }
        if project_id is not None:
            analysis_row["project_id"] = project_id
        analysis_id = insert_row_on(connection, "text_analyses", analysis_row)
        entity_ids = {}
        for mention in fields.get("mentions") or []:
            key = (mention["type"], mention["normalized_name"])
            if key in entity_ids:
                continue
            existing = fetch_first_on(
                connection,
                "entities",
                {
                    "entity_type_id": type_rows[mention["type"]]["id"],
                    "normalized_name": mention["normalized_name"],
                },
            )
            if existing is not None:
                entity_ids[key] = existing["id"]
                continue
            entity_ids[key] = insert_row_on(
                connection,
                "entities",
                {
                    "entity_type_id": type_rows[mention["type"]]["id"],
                    "status_id": candidate["id"],
                    "canonical_name": mention["canonical_name"],
                    "normalized_name": mention["normalized_name"],
                },
            )
        seen_spans = set()
        for mention in fields.get("mentions") or []:
            entity_id = entity_ids[(mention["type"], mention["normalized_name"])]
            span_key = (entity_id, mention["start_offset"], mention["end_offset"])
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)
            mention_id = insert_row_on(
                connection,
                "entity_mentions",
                {
                    "analysis_id": analysis_id,
                    "entity_id": entity_id,
                    "mention_text": mention["mention_text"],
                    "start_offset": mention["start_offset"],
                    "end_offset": mention["end_offset"],
                    "confidence": _as_confidence(mention["confidence"]),
                },
            )
            if mention.get("occurred_at") is not None:
                insert_row_on(
                    connection,
                    "entity_mention_times",
                    {
                        "mention_id": mention_id,
                        "occurred_at": mention["occurred_at"],
                    },
                )
        primary_used = False
        seen_topics = set()
        for topic in fields.get("topics") or []:
            topic_row = _lookup_or_create_topic(connection, topic)
            topic_id = topic_row["id"]
            if topic_id in seen_topics:
                continue
            seen_topics.add(topic_id)
            is_primary = bool(topic.get("is_primary")) and not primary_used
            if is_primary:
                primary_used = True
            insert_row_on(
                connection,
                "text_analysis_topics",
                {
                    "analysis_id": analysis_id,
                    "topic_id": topic_id,
                    "is_primary": is_primary,
                    "confidence": _as_confidence(topic.get("confidence") or 1),
                    "mention_text": _as_mention_text(topic.get("mention_text")),
                },
            )
        if polarity_row is not None and sentiment_intensity is not None:
            insert_row_on(
                connection,
                "text_analysis_sentiments",
                {
                    "analysis_id": analysis_id,
                    "polarity_id": polarity_row["id"],
                    "intensity_id": sentiment_intensity["id"],
                    "mention_text": _as_mention_text(sentiment.get("mention_text")),
                },
            )
        seen_emotions = set()
        for item, (emotion_row, intensity_row) in zip(
            fields.get("emotions") or [],
            emotion_rows,
        ):
            if emotion_row["id"] in seen_emotions:
                continue
            seen_emotions.add(emotion_row["id"])
            insert_row_on(
                connection,
                "text_analysis_emotions",
                {
                    "analysis_id": analysis_id,
                    "emotion_id": emotion_row["id"],
                    "intensity_id": intensity_row["id"],
                    "mention_text": _as_mention_text(item.get("mention_text")),
                },
            )
        primary_discourse = False
        seen_discourses = set()
        for item in fields.get("discourses") or []:
            type_row = _lookup_or_create_discourse_type(connection, item)
            type_id = type_row["id"]
            if type_id in seen_discourses:
                continue
            seen_discourses.add(type_id)
            is_primary = bool(item.get("is_primary")) and not primary_discourse
            if is_primary:
                primary_discourse = True
            analysis_discourse_id = insert_row_on(
                connection,
                "text_analysis_discourses",
                {
                    "analysis_id": analysis_id,
                    "discourse_type_id": type_id,
                    "is_primary": is_primary,
                    "confidence": _as_confidence(item.get("confidence") or 1),
                    "mention_text": _as_mention_text(item.get("mention_text")),
                },
            )
            seen_slots = set()
            for slot_name, slot_value in (item.get("slots") or {}).items():
                name = str(slot_name or "").strip()
                value = _as_mention_text(slot_value)
                if not name or not value or name in seen_slots:
                    continue
                seen_slots.add(name)
                insert_row_on(
                    connection,
                    "text_analysis_discourse_slots",
                    {
                        "analysis_discourse_id": analysis_discourse_id,
                        "slot_name": name[:100],
                        "slot_value": value[:300],
                    },
                )
        primary_intent = False
        seen_intents = set()
        for item in fields.get("intents") or []:
            intent_id = intent_rows[item["code"]]["id"]
            if intent_id in seen_intents:
                continue
            seen_intents.add(intent_id)
            is_primary = bool(item.get("is_primary")) and not primary_intent
            if is_primary:
                primary_intent = True
            analysis_intent_id = insert_row_on(
                connection,
                "text_analysis_intents",
                {
                    "analysis_id": analysis_id,
                    "intent_id": intent_id,
                    "is_primary": is_primary,
                    "confidence": _as_confidence(item.get("confidence") or 1),
                    "mention_text": _as_mention_text(item.get("mention_text")),
                },
            )
            seen_slots = set()
            for slot_name, slot_value in (item.get("slots") or {}).items():
                name = str(slot_name or "").strip()
                value = _as_mention_text(slot_value)
                if not name or not value or name in seen_slots:
                    continue
                seen_slots.add(name)
                insert_row_on(
                    connection,
                    "text_analysis_intent_slots",
                    {
                        "analysis_intent_id": analysis_intent_id,
                        "slot_name": name[:100],
                        "slot_value": value[:300],
                    },
                )
        primary_rhetoric = False
        seen_rhetorics = set()
        document_meaning = str(fields.get("intended_meaning") or "").strip()
        for item in fields.get("rhetorics") or []:
            rhetoric_id = rhetoric_rows[item["code"]]["id"]
            if rhetoric_id in seen_rhetorics:
                continue
            seen_rhetorics.add(rhetoric_id)
            is_primary = bool(item.get("is_primary")) and not primary_rhetoric
            if is_primary:
                primary_rhetoric = True
            meaning = str(item.get("intended_meaning") or "").strip()
            if is_primary and not meaning:
                meaning = document_meaning
            analysis_rhetoric_id = insert_row_on(
                connection,
                "text_analysis_rhetorics",
                {
                    "analysis_id": analysis_id,
                    "rhetoric_type_id": rhetoric_id,
                    "is_primary": is_primary,
                    "confidence": _as_confidence(item.get("confidence") or 1),
                    "mention_text": _as_mention_text(item.get("mention_text")),
                    "intended_meaning": meaning,
                },
            )
            seen_slots = set()
            for slot_name, slot_value in (item.get("slots") or {}).items():
                name = str(slot_name or "").strip()
                value = _as_mention_text(slot_value)
                if not name or not value or name in seen_slots:
                    continue
                seen_slots.add(name)
                insert_row_on(
                    connection,
                    "text_analysis_rhetoric_slots",
                    {
                        "analysis_rhetoric_id": analysis_rhetoric_id,
                        "slot_name": name[:100],
                        "slot_value": value[:300],
                    },
                )
        fact_count = _insert_facts_on(connection, analysis_id, fields.get("facts") or [])
        quote_count = _insert_quotes_on(
            connection, analysis_id, fields.get("quotes") or []
        )
        keyword_count = _insert_keywords_on(
            connection,
            analysis_id,
            fields.get("keywords") or [],
            {
                "source_type_id": source_type_row["id"],
                "source_id": resolved_source_id,
                "project_id": project_id,
                "created_by_user_id": source_user_id,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "TextAnalysis",
            analysis_id,
            None,
            {
                "source_type": source_type,
                "source_id": resolved_source_id,
                "mention_count": len(seen_spans),
                "topic_count": len(seen_topics),
                "discourse_count": len(seen_discourses),
                "intent_count": len(seen_intents),
                "rhetoric_count": len(seen_rhetorics),
                "fact_count": fact_count,
                "quote_count": quote_count,
                "keyword_count": keyword_count,
            },
        )
        return analysis_id

    new_id = run_query(work)
    stored = fetch_text_analysis_record(new_id)
    return _payload_from_analysis(stored)


def insert_text_analysis_facts(analysis_id: int, facts: list, created_by: int) -> list:
    """فکت‌های تأییدشده را روی تحلیل موجود می‌نویسد؛ اگر از قبل باشد همان را می‌دهد."""
    require_text_analysis_access(analysis_id, created_by)
    existing = fetch_text_analysis_facts_records(analysis_id)
    if existing or not facts:
        return existing
    for item in facts:
        _lookup_fact(item)

    def work(connection):
        return _insert_facts_on(connection, analysis_id, facts)

    run_query(work)
    return fetch_text_analysis_facts_records(analysis_id)


def insert_text_analysis_quotes(analysis_id: int, quotes: list, created_by: int) -> list:
    """نقل‌قول‌های تأییدشده را روی تحلیل موجود می‌نویسد؛ اگر از قبل باشد همان را می‌دهد."""
    require_text_analysis_access(analysis_id, created_by)
    existing = fetch_text_analysis_quotes_records(analysis_id)
    if existing or not quotes:
        return existing
    for item in quotes:
        _lookup_quote(item)

    def work(connection):
        return _insert_quotes_on(connection, analysis_id, quotes)

    run_query(work)
    return fetch_text_analysis_quotes_records(analysis_id)


insert_text_analysis = logged_step("insert")(insert_text_analysis)
insert_text_analysis_facts = logged_step("insert")(insert_text_analysis_facts)
insert_text_analysis_quotes = logged_step("insert")(insert_text_analysis_quotes)
fetch_text_analysis = logged_step("fetch")(fetch_text_analysis)
require_text_analysis_access = logged_step("authorize")(require_text_analysis_access)
fetch_text_analyses_for_actor = logged_step("fetch")(fetch_text_analyses_for_actor)
