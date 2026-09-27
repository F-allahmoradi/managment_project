"""زنجیرهٔ استخراج موبایل: لایه‌ها، ذخیرهٔ پیشنهادی، بعد امبدینگ.

NER و NLP اینجا INSERT ندارند. ذخیره با save_text_analysis در crud است.
شکست یک لایه بقیه را دور نمی‌ریزد.
هر ابزار MCP یک لایه است؛ نتیجه با کش و پیشرفت لایه‌به‌لایه برمی‌گردد.
"""

from collections import OrderedDict
from typing import Callable, NamedTuple
import threading
import time
import uuid

from hub.pool import WorkerError

_SOURCE_TYPES = frozenset({"message", "meeting", "content"})
_CACHE_TTL_SECONDS = 45 * 60
_CACHE_MAX = 400
_JOB_TTL_SECONDS = 45 * 60
_MEANING_KEYS = frozenset({"sentiment", "discourse", "intent"})


class Layer(NamedTuple):
    """یک ابزار استخراج ثبت‌شده در MCP."""

    key: str
    domain: str
    tool: str
    label: str


EXTRACT_LAYERS = (
    Layer("rhetoric", "ner", "extract_rhetoric", "بیان"),
    Layer("entities", "ner", "extract_entities", "موجودیت‌ها"),
    Layer("keywords", "ner", "extract_keywords", "کلمه‌های کلیدی"),
    Layer("topics", "ner", "extract_topics", "موضوع‌ها"),
    Layer("sentiment", "ner", "extract_sentiment", "قطبیت و هیجان"),
    Layer("discourse", "ner", "extract_discourse", "ژانرها"),
    Layer("intent", "ner", "extract_intent", "نیت‌ها"),
    Layer("facts", "nlp", "extract_facts", "فکت‌ها"),
    Layer("quotes", "nlp", "extract_quotes", "نقل‌قول‌ها"),
    Layer("frame", "nlp", "extract_frame", "قاب مسئله"),
)

_CACHE_LOCK = threading.Lock()
_LAYER_CACHE: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()
_JOBS_LOCK = threading.Lock()
_JOBS: dict[str, "_PreviewJob"] = {}
_RUNNING: dict[tuple, str] = {}


def planned_layers(domains: tuple) -> list[Layer]:
    """لایه‌هایی که روی این سرور واقعاً صدا زده می‌شوند."""
    available = set(domains)
    return [item for item in EXTRACT_LAYERS if item.domain in available]


def plan_payload(domains: tuple) -> list[dict]:
    """فهرست لایه‌ها برای نمایش پیشرفت."""
    return [
        {"key": item.key, "label": item.label, "domain": item.domain, "tool": item.tool}
        for item in planned_layers(domains)
    ]


def reset_extract_runtime() -> None:
    """کش و کارهای در جریان را خالی می‌کند؛ مخصوص آزمون."""
    with _CACHE_LOCK:
        _LAYER_CACHE.clear()
    with _JOBS_LOCK:
        _JOBS.clear()
        _RUNNING.clear()


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
    facts_layer = layers.get("facts") or {}
    sentiment = None
    if isinstance(sentiment_layer, dict) and sentiment_layer.get("status") != "error":
        sentiment = sentiment_layer.get("sentiment")
    intended = None
    if isinstance(rhetoric_layer, dict) and rhetoric_layer.get("status") != "error":
        intended = str(rhetoric_layer.get("intended_meaning") or "").strip() or None
    packed = {
        "source_type": source_type,
        "source_id": source_id,
        "mentions": mentions,
        "entities": layer_items(layers.get("entities"), "entities"),
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
    if isinstance(facts_layer, dict) and facts_layer.get("status") != "error":
        packed["explicitness"] = facts_layer.get("explicitness")
        packed["explicitness_name"] = facts_layer.get("explicitness_name")
    return packed


def _frame_of(result):
    """قاب مسئله را اگر لایه موفق باشد برمی‌گرداند."""
    if not isinstance(result, dict) or result.get("status") == "error":
        return None
    frame = result.get("frame")
    return frame if isinstance(frame, dict) else None


def _cache_key(source_type: str, source_id: int, tool: str, meaning: str) -> tuple:
    return (source_type, int(source_id), tool, meaning or "")


def _cache_get(source_type: str, source_id: int, tool: str, meaning: str = ""):
    key = _cache_key(source_type, source_id, tool, meaning)
    now = time.monotonic()
    with _CACHE_LOCK:
        item = _LAYER_CACHE.get(key)
        if item is None:
            return None
        stored_at, payload = item
        if now - stored_at > _CACHE_TTL_SECONDS:
            _LAYER_CACHE.pop(key, None)
            return None
        _LAYER_CACHE.move_to_end(key)
        return payload


def _cache_put(source_type: str, source_id: int, tool: str, meaning: str, payload: dict) -> None:
    if not isinstance(payload, dict) or payload.get("status") == "error":
        return
    key = _cache_key(source_type, source_id, tool, meaning)
    with _CACHE_LOCK:
        _LAYER_CACHE[key] = (time.monotonic(), payload)
        _LAYER_CACHE.move_to_end(key)
        while len(_LAYER_CACHE) > _CACHE_MAX:
            _LAYER_CACHE.popitem(last=False)


def _invoke_layer(pool, layer: Layer, source: dict, actor_id: int, meaning: str | None) -> tuple[dict, bool]:
    """نتیجهٔ کش‌شده یا اجرای تازهٔ یک ابزار MCP را برمی‌گرداند."""
    extra = meaning if layer.key in _MEANING_KEYS else ""
    cached = _cache_get(source["source_type"], source["source_id"], layer.tool, extra or "")
    if cached is not None:
        return cached, True
    arguments = dict(source)
    if extra:
        arguments["intended_meaning"] = extra
    result = _invoke(pool, layer.domain, layer.tool, arguments, actor_id)
    _cache_put(source["source_type"], source["source_id"], layer.tool, extra or "", result)
    return result, False


def _layers_from_cache(source_type: str, source_id: int, domains: tuple):
    """اگر همهٔ لایه‌های برنامه در کش باشند همان‌ها را برمی‌گرداند."""
    plan = planned_layers(domains)
    if not plan:
        return None
    layers = {}
    meaning = ""
    for layer in plan:
        extra = meaning if layer.key in _MEANING_KEYS else ""
        payload = _cache_get(source_type, source_id, layer.tool, extra)
        if payload is None:
            return None
        layers[layer.key] = payload
        if layer.key == "rhetoric":
            meaning = meaning_of(payload) or ""
    return layers


def _collect_layers(
    pool,
    domains: tuple,
    actor_id: int,
    source_type: str,
    source_id: int,
    on_progress: Callable | None = None,
) -> dict:
    """لایه‌های استخراج را بدون ذخیره برمی‌گرداند."""
    if source_type not in _SOURCE_TYPES:
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "منبع تحلیل باید پیام یا جلسه یا محتوا باشد",
        }
    if "ner" not in domains:
        return {
            "status": "error",
            "error_code": "DOMAIN_UNAVAILABLE",
            "message": "استخراج موجودیت روی این سرور فعال نیست",
        }
    plan = planned_layers(domains)
    source = {"source_type": source_type, "source_id": int(source_id)}
    cached_layers = _layers_from_cache(source_type, int(source_id), domains)
    if cached_layers is not None:
        if on_progress:
            for layer in plan:
                on_progress("done", layer, cached_layers[layer.key], True)
        return _finish_layers(source_type, int(source_id), cached_layers)

    layers: dict = {}
    layers_lock = threading.Lock()

    def run_one(layer: Layer, meaning: str | None) -> None:
        if on_progress:
            on_progress("start", layer, None, False)
        result, cached = _invoke_layer(pool, layer, source, actor_id, meaning)
        with layers_lock:
            layers[layer.key] = result
        if on_progress:
            on_progress("done", layer, result, cached)

    rhetoric_layer = next(item for item in plan if item.key == "rhetoric")
    run_one(rhetoric_layer, None)
    meaning = meaning_of(layers.get("rhetoric"))
    ner_rest = [item for item in plan if item.domain == "ner" and item.key != "rhetoric"]
    nlp_steps = [item for item in plan if item.domain == "nlp"]

    def run_group(steps: list[Layer]) -> None:
        for layer in steps:
            extra = meaning if layer.key in _MEANING_KEYS else None
            run_one(layer, extra)

    workers = []
    if ner_rest:
        thread = threading.Thread(target=run_group, args=(ner_rest,), daemon=True)
        workers.append(thread)
        thread.start()
    if nlp_steps:
        thread = threading.Thread(target=run_group, args=(nlp_steps,), daemon=True)
        workers.append(thread)
        thread.start()
    if not workers:
        run_group([])
    for thread in workers:
        thread.join()
    return _finish_layers(source_type, int(source_id), layers)


def _finish_layers(source_type: str, source_id: int, layers: dict) -> dict:
    """خطاهای لایه و فیلدهای ذخیره‌شدنی را جمع می‌کند."""
    layer_errors = {
        name: result.get("message") or "لایه شکست خورد"
        for name, result in layers.items()
        if isinstance(result, dict) and result.get("status") == "error"
    }
    if layers and len(layer_errors) == len(layers):
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
        "phase": "done",
        "message": "موارد استخراج‌شده آمادهٔ بازبینی است",
        "fields": collected["fields"],
        "layer_errors": collected["layer_errors"],
        "planned_layers": plan_payload(domains),
        "completed_layers": [item.key for item in planned_layers(domains)],
        "current_layers": [],
    }


def start_preview_job(pool, domains: tuple, actor_id: int, source_type: str, source_id: int) -> dict:
    """استخراج را در پس‌زمینه شروع می‌کند تا کلاینت پیشرفت را پول کند."""
    if source_type not in _SOURCE_TYPES:
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "منبع تحلیل باید پیام یا جلسه یا محتوا باشد",
        }
    if "ner" not in domains:
        return {
            "status": "error",
            "error_code": "DOMAIN_UNAVAILABLE",
            "message": "استخراج موجودیت روی این سرور فعال نیست",
        }
    _prune_jobs()
    run_key = (int(actor_id), source_type, int(source_id))
    with _JOBS_LOCK:
        existing_id = _RUNNING.get(run_key)
        if existing_id and existing_id in _JOBS:
            return _job_snapshot(_JOBS[existing_id])
        cached = _layers_from_cache(source_type, int(source_id), domains)
        if cached is not None:
            job = _PreviewJob(actor_id, source_type, int(source_id), domains)
            job.layers = dict(cached)
            job.completed = [item.key for item in planned_layers(domains)]
            job.phase = "done"
            job.from_cache = True
            job.final = _finish_layers(source_type, int(source_id), cached)
            _JOBS[job.id] = job
            return _job_snapshot(job)
        job = _PreviewJob(actor_id, source_type, int(source_id), domains)
        _JOBS[job.id] = job
        _RUNNING[run_key] = job.id
    thread = threading.Thread(
        target=_run_preview_job,
        args=(job, pool, domains, actor_id, source_type, int(source_id), run_key),
        daemon=True,
    )
    thread.start()
    return _job_snapshot(job)


def get_preview_job(job_id: str, actor_id: int) -> dict:
    """وضعیت یک کار استخراج را برای پولینگ برمی‌گرداند."""
    _prune_jobs()
    with _JOBS_LOCK:
        job = _JOBS.get(str(job_id or "").strip())
    if job is None:
        return {
            "status": "error",
            "error_code": "JOB_NOT_FOUND",
            "message": "کار استخراج پیدا نشد",
        }
    if int(job.actor_id) != int(actor_id):
        return {
            "status": "error",
            "error_code": "PERMISSION_DENIED",
            "message": "به این استخراج دسترسی ندارید",
        }
    return _job_snapshot(job)


def _run_preview_job(job, pool, domains, actor_id, source_type, source_id, run_key) -> None:
    """لایه‌ها را اجرا می‌کند و پیشرفت را روی کار می‌نویسد."""

    def on_progress(event: str, layer: Layer, result, cached: bool) -> None:
        with job.lock:
            if event == "start":
                if layer.key not in [item.key for item in job.active]:
                    job.active.append(layer)
                return
            job.active = [item for item in job.active if item.key != layer.key]
            job.layers[layer.key] = result
            if layer.key not in job.completed:
                job.completed.append(layer.key)
            if isinstance(result, dict) and result.get("status") == "error":
                job.layer_errors[layer.key] = result.get("message") or "لایه شکست خورد"

    try:
        collected = _collect_layers(
            pool,
            domains,
            actor_id,
            source_type,
            source_id,
            on_progress=on_progress,
        )
        with job.lock:
            job.final = collected
            job.active = []
            if collected.get("status") == "success":
                job.phase = "done"
            else:
                job.phase = "error"
                job.message = collected.get("message") or "استخراج انجام نشد"
                job.error_code = collected.get("error_code")
    except Exception:
        with job.lock:
            job.phase = "error"
            job.message = "استخراج انجام نشد"
            job.error_code = "WORKER_ERROR"
            job.active = []
    finally:
        with _JOBS_LOCK:
            if _RUNNING.get(run_key) == job.id:
                _RUNNING.pop(run_key, None)


def _job_snapshot(job) -> dict:
    """پاکت پیشرفت را برای کلاینت می‌سازد."""
    with job.lock:
        layers = dict(job.layers)
        phase = job.phase
        completed = list(job.completed)
        active = list(job.active)
        errors = dict(job.layer_errors)
        from_cache = job.from_cache
        job_id = job.id
        source_type = job.source_type
        source_id = job.source_id
        domains = job.domains
        final = job.final
        message = job.message
        error_code = job.error_code
    if phase == "error" and final and final.get("status") == "error":
        payload = dict(final)
        payload["job_id"] = job_id
        payload["phase"] = "error"
        payload["planned_layers"] = plan_payload(domains)
        payload["completed_layers"] = completed
        payload["current_layers"] = []
        payload["cached"] = from_cache
        return payload
    fields = pack_save_fields(source_type, source_id, layers)
    current = [{"key": item.key, "label": item.label} for item in active]
    if phase == "done":
        status_message = "موارد استخراج‌شده آمادهٔ بازبینی است"
        if from_cache:
            status_message = "موارد استخراج‌شده از کش آمد"
    elif current:
        labels = [item["label"] for item in current]
        status_message = "در حال استخراج " + " و ".join(labels)
    else:
        status_message = "در حال آماده‌سازی استخراج"
    return {
        "status": "success",
        "job_id": job_id,
        "phase": phase,
        "cached": from_cache,
        "message": status_message if phase != "error" else (message or status_message),
        "error_code": error_code,
        "fields": fields,
        "layer_errors": errors,
        "planned_layers": plan_payload(domains),
        "completed_layers": completed,
        "current_layers": current,
        "source_type": source_type,
        "source_id": source_id,
    }


def _prune_jobs() -> None:
    """کارهای قدیمی را از حافظه برمی‌دارد."""
    now = time.monotonic()
    with _JOBS_LOCK:
        stale = [
            job_id
            for job_id, job in _JOBS.items()
            if now - job.created_at > _JOB_TTL_SECONDS
        ]
        for job_id in stale:
            job = _JOBS.pop(job_id, None)
            if job is None:
                continue
            run_key = (job.actor_id, job.source_type, job.source_id)
            if _RUNNING.get(run_key) == job_id:
                _RUNNING.pop(run_key, None)


class _PreviewJob:
    """وضعیت یک استخراج در جریان برای پولینگ."""

    def __init__(self, actor_id: int, source_type: str, source_id: int, domains: tuple) -> None:
        self.id = uuid.uuid4().hex
        self.actor_id = int(actor_id)
        self.source_type = source_type
        self.source_id = int(source_id)
        self.domains = domains
        self.lock = threading.Lock()
        self.phase = "running"
        self.layers: dict = {}
        self.completed: list[str] = []
        self.active: list[Layer] = []
        self.layer_errors: dict = {}
        self.from_cache = False
        self.final = None
        self.message = ""
        self.error_code = None
        self.created_at = time.monotonic()


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
