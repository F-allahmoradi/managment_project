"""زنجیرهٔ استخراج موبایل: لایه‌ها، ذخیرهٔ پیشنهادی، بعد امبدینگ.

NER و NLP اینجا INSERT ندارند. ذخیره با save_text_analysis در crud است.
شکست یک لایه بقیه را دور نمی‌ریزد.
"""

from hub.pool import WorkerError

_SOURCE_TYPES = frozenset({"message", "meeting"})


def meaning_of(rhetoric) -> str | None:
    """معنای مقصود را اگر بیان غیرصریح باشد برمی‌گرداند."""
    if not isinstance(rhetoric, dict) or rhetoric.get("status") == "error":
        return None
    meaning = str(rhetoric.get("intended_meaning") or "").strip()
    hits = rhetoric.get("rhetorics") or []
    primary = next((item for item in hits if isinstance(item, dict) and item.get("is_primary")), None)
    code = primary.get("code") if isinstance(primary, dict) else None
    if not meaning or code == "literal":
        return None
    return meaning


def drop_entity_copy_keywords(keywords: list, mentions: list) -> list:
    """عبارتی که همان ذکر موجودیت است کلمهٔ کلیدی جدا نیست."""
    names = set()
    for mention in mentions:
        if not isinstance(mention, dict):
            continue
        for key in ("normalized_name", "mention_text", "canonical_name"):
            value = str(mention.get(key) or "").strip()
            if value:
                names.add(value)
    cleaned = []
    for item in keywords:
        if not isinstance(item, dict):
            continue
        phrase = str(item.get("phrase") or "").strip()
        if phrase and phrase not in names:
            cleaned.append(item)
    return cleaned


def layer_items(result, key: str) -> list:
    """فهرست یک لایه را اگر موفق باشد برمی‌گرداند."""
    if not isinstance(result, dict) or result.get("status") == "error":
        return []
    items = result.get(key) or []
    return items if isinstance(items, list) else []


def pack_save_fields(source_type: str, source_id: int, layers: dict) -> dict:
    """خروجی لایه‌ها را به ورودی save_text_analysis تبدیل می‌کند."""
    mentions = layer_items(layers.get("entities"), "mentions")
    keywords = drop_entity_copy_keywords(
        layer_items(layers.get("keywords"), "keywords"),
        mentions,
    )
    sentiment_layer = layers.get("sentiment") or {}
    rhetoric_layer = layers.get("rhetoric") or {}
    sentiment = None
    if isinstance(sentiment_layer, dict) and sentiment_layer.get("status") != "error":
        sentiment = sentiment_layer.get("sentiment")
    intended = None
    if isinstance(rhetoric_layer, dict) and rhetoric_layer.get("status") != "error":
        intended = str(rhetoric_layer.get("intended_meaning") or "").strip() or None
    return {
        "source_type": source_type,
        "source_id": source_id,
        "mentions": mentions,
        "keywords": keywords,
        "topics": layer_items(layers.get("topics"), "topics"),
        "sentiment": sentiment,
        "emotions": layer_items(sentiment_layer, "emotions"),
        "discourses": layer_items(layers.get("discourse"), "discourses"),
        "intents": layer_items(layers.get("intent"), "intents"),
        "rhetorics": layer_items(rhetoric_layer, "rhetorics"),
        "facts": layer_items(layers.get("facts"), "facts"),
        "quotes": layer_items(layers.get("quotes"), "quotes"),
        "frame": _frame_of(layers.get("frame")),
        "intended_meaning": intended,
    }


def _frame_of(result):
    """قاب مسئله را اگر لایه موفق باشد برمی‌گرداند."""
    if not isinstance(result, dict) or result.get("status") == "error":
        return None
    frame = result.get("frame")
    return frame if isinstance(frame, dict) else None


def _collect_layers(pool, domains: tuple, actor_id: int, source_type: str, source_id: int) -> dict:
    """لایه‌های استخراج را بدون ذخیره برمی‌گرداند."""
    if source_type not in _SOURCE_TYPES:
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "منبع تحلیل باید پیام یا جلسه باشد",
        }
    if "ner" not in domains:
        return {
            "status": "error",
            "error_code": "DOMAIN_UNAVAILABLE",
            "message": "استخراج موجودیت روی این سرور فعال نیست",
        }
    source = {"source_type": source_type, "source_id": int(source_id)}
    rhetoric = _invoke(pool, "ner", "extract_rhetoric", source, actor_id)
    meaning = meaning_of(rhetoric)
    meaning_args = dict(source)
    if meaning:
        meaning_args["intended_meaning"] = meaning
    layers = {
        "rhetoric": rhetoric,
        "entities": _invoke(pool, "ner", "extract_entities", source, actor_id),
        "keywords": _invoke(pool, "ner", "extract_keywords", source, actor_id),
        "topics": _invoke(pool, "ner", "extract_topics", source, actor_id),
        "sentiment": _invoke(pool, "ner", "extract_sentiment", meaning_args, actor_id),
        "discourse": _invoke(pool, "ner", "extract_discourse", meaning_args, actor_id),
        "intent": _invoke(pool, "ner", "extract_intent", meaning_args, actor_id),
    }
    if "nlp" in domains:
        layers["facts"] = _invoke(pool, "nlp", "extract_facts", source, actor_id)
        layers["quotes"] = _invoke(pool, "nlp", "extract_quotes", source, actor_id)
        layers["frame"] = _invoke(pool, "nlp", "extract_frame", source, actor_id)
    layer_errors = {
        name: result.get("message") or "لایه شکست خورد"
        for name, result in layers.items()
        if isinstance(result, dict) and result.get("status") == "error"
    }
    if len(layer_errors) == len(layers):
        first = next(iter(layers.values()))
        return {
            "status": "error",
            "error_code": first.get("error_code") or "DOMAIN_UNAVAILABLE",
            "message": first.get("message") or "استخراج انجام نشد",
            "layer_errors": layer_errors,
        }
    return {
        "status": "success",
        "source_type": source_type,
        "source_id": int(source_id),
        "fields": pack_save_fields(source_type, int(source_id), layers),
        "layer_errors": layer_errors,
    }


def preview_source(pool, domains: tuple, actor_id: int, source_type: str, source_id: int) -> dict:
    """متن ذخیره‌شده را استخراج می‌کند و موارد را بدون نوشتن در پایگاه برمی‌گرداند."""
    collected = _collect_layers(pool, domains, actor_id, source_type, source_id)
    if collected.get("status") != "success":
        return collected
    return {
        "status": "success",
        "message": "موارد استخراج‌شده آمادهٔ بازبینی است",
        "fields": collected["fields"],
        "layer_errors": collected["layer_errors"],
    }


def commit_analysis(pool, domains: tuple, actor_id: int, fields: dict) -> dict:
    """موارد تأییدشده را ذخیره می‌کند و در صورت آمادگی امبد می‌کند."""
    if not isinstance(fields, dict):
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "موارد استخراج لازم است",
        }
    saved = _invoke(pool, "crud", "save_text_analysis", fields, actor_id)
    if saved.get("status") != "success":
        return saved
    analysis_id = saved.get("id")
    if "embedding" in domains and analysis_id:
        indexed = _invoke(
            pool,
            "embedding",
            "index_text_analysis",
            {"analysis_id": int(analysis_id)},
            actor_id,
        )
        saved["embedding"] = indexed
    return saved


def analyze_source(pool, domains: tuple, actor_id: int, source_type: str, source_id: int) -> dict:
    """متن منبع را استخراج می‌کند، به‌صورت پیشنهادی ذخیره می‌کند، بعد امبد می‌کند."""
    collected = _collect_layers(pool, domains, actor_id, source_type, source_id)
    if collected.get("status") != "success":
        return collected
    layer_errors = collected.get("layer_errors") or {}
    saved = _invoke(
        pool,
        "crud",
        "save_text_analysis",
        collected["fields"],
        actor_id,
    )
    if saved.get("status") != "success":
        saved["layer_errors"] = layer_errors
        return saved
    if layer_errors:
        saved["layer_errors"] = layer_errors
    analysis_id = saved.get("id")
    if "embedding" in domains and analysis_id:
        indexed = _invoke(
            pool,
            "embedding",
            "index_text_analysis",
            {"analysis_id": int(analysis_id)},
            actor_id,
        )
        saved["embedding"] = indexed
    return saved


def _invoke(pool, domain: str, tool: str, arguments: dict, actor_id: int) -> dict:
    """یک ابزار دامنه را صدا می‌زند و خطای فرآیند را مثل لایهٔ شکست‌خورده برمی‌گرداند."""
    try:
        result = pool.call(domain, tool, arguments, actor_id)
    except WorkerError as exc:
        return {
            "status": "error",
            "error_code": exc.error_code,
            "message": exc.message,
        }
    if not isinstance(result, dict):
        return {"status": "error", "error_code": "WORKER_ERROR", "message": "پاسخ استخراج نامعتبر بود"}
    return result
