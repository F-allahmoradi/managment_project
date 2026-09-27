"""سرور HTTP محلی برای تست استخراج متن پروژه در مرورگر.

stdio مخصوص کلاینت MCP می‌ماند. اینجا فقط localhost است.
استخراج INSERT ندارد. ذخیره جدا با وضعیت پیشنهادی به CRUD می‌رود.
"""

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import sys
import time
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path, load_crud_symbol, load_embedding_symbol

ensure_import_path()

from business_logic.extractor import (
    extract_discourse,
    extract_entities,
    extract_intent,
    extract_keywords,
    extract_rhetoric,
    extract_sentiment,
    extract_topics,
)
from business_logic.layers.span import drop_entity_copy_keywords
from business_logic.normalizer import normalize_text
from errors.crud import format_crud_error, format_error
from logging_module import log_operation, setup_logging
from playground.config import bind_playground_actor, load_playground_config
from playground.speech_check import catalog_payload, combine_check
from schemas.output import (
    ExtractDiscourseOutput,
    ExtractEntitiesOutput,
    ExtractIntentOutput,
    ExtractKeywordsOutput,
    ExtractRhetoricOutput,
    ExtractSentimentOutput,
    ExtractTopicsOutput,
)
from tests.sample import SAMPLE_TEXT

_SAVE_INPUT = None


def _save_input_cls():
    """اسکیمای ذخیره کراد را یک‌بار، جدا از schemas همنام ner، می‌آورد."""
    global _SAVE_INPUT
    if _SAVE_INPUT is None:
        _SAVE_INPUT = load_crud_symbol(
            "schemas.crud.text_analysis",
            "SaveTextAnalysisInput",
        )
    return _SAVE_INPUT


def _try_index(analysis_id: int):
    """اگر امبدینگ در دسترس باشد تحلیل ذخیره‌شده را برداری می‌کند."""
    try:
        index_fn = load_embedding_symbol("business_logic.indexer", "index_analysis")
        from auth.gate import require_permission

        actor = require_permission("TextAnalysis", "Create")
        return index_fn(analysis_id, actor["id"])
    except Exception as exc:
        packed = format_error(exc)
        return {
            "status": packed.get("status") or "error",
            "error_code": packed.get("error_code"),
            "message": packed.get("message") or "برداری انجام نشد",
        }


_STATIC = Path(__file__).resolve().parent / "static"
_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def _read_json_body(handler: BaseHTTPRequestHandler, limit: int = 200_000) -> dict:
    """بدنه JSON درخواست را می‌خواند."""
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    if length > limit:
        raise ValueError("بدنه درخواست بزرگ‌تر از حد مجاز است")
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("بدنه باید شیء JSON باشد")
    return payload


_LAYERS = {
    "entities": extract_entities,
    "keywords": extract_keywords,
    "topics": extract_topics,
    "sentiment": extract_sentiment,
    "discourse": extract_discourse,
    "intent": extract_intent,
    "rhetoric": extract_rhetoric,
}
_LAYER_LABELS = {
    "entities": "موجودیت",
    "keywords": "کلمهٔ کلیدی",
    "topics": "موضوع",
    "sentiment": "احساس",
    "discourse": "ژانر",
    "intent": "نیت",
    "rhetoric": "بیان",
}
_TOOL_BY_LAYER = {
    "entities": "extract_entities",
    "keywords": "extract_keywords",
    "topics": "extract_topics",
    "sentiment": "extract_sentiment",
    "discourse": "extract_discourse",
    "intent": "extract_intent",
    "rhetoric": "extract_rhetoric",
}
_MEANING_LAYERS = frozenset({"sentiment", "discourse", "intent"})
# این چهار تا به خروجی هم نیاز ندارند و با هم اجرا می‌شوند.
_FREE_LAYERS = ("rhetoric", "entities", "keywords", "topics")
# این سه تا معنای مقصود را از بیان می‌گیرند و قبل از برگشتن بیان شروع نمی‌شوند.
_AFTER_RHETORIC = ("sentiment", "discourse", "intent")


def _run_traced(name: str, text: str, intended_meaning: str | None = None) -> dict:
    """یک لایه را با عملیات لاگ اجرا می‌کند تا نام ابزار و مدت در پاسخ بیاید."""
    tool = _TOOL_BY_LAYER[name]
    with log_operation(tool) as operation:
        try:
            fn = _LAYERS[name]
            if intended_meaning and name in _MEANING_LAYERS:
                result = fn(text, intended_meaning=intended_meaning)
            else:
                result = fn(text)
        except Exception as exc:
            operation.status = "error"
            packed = format_error(exc)
            packed["layer"] = name
            packed["tool"] = tool
            return operation.attach(packed)
        payload = result.model_dump()
        payload["normalized_text"] = normalize_text(text)
        payload["layer"] = name
        payload["tool"] = tool
        return operation.attach(payload)


def _dump_layer(name: str, text: str, intended_meaning: str | None = None) -> dict:
    """یک لایه را اجرا و به JSON تبدیل می‌کند."""
    return _run_traced(name, text, intended_meaning=intended_meaning)


def _meaning_of(rhetoric_payload) -> str | None:
    """معنای مقصود را اگر بیان غیرصریح باشد برمی‌گرداند."""
    if rhetoric_payload is None:
        return None
    if hasattr(rhetoric_payload, "intended_meaning"):
        meaning = str(rhetoric_payload.intended_meaning or "").strip()
        hits = getattr(rhetoric_payload, "rhetorics", None) or []
        primary = next((item for item in hits if getattr(item, "is_primary", False)), None)
        code = getattr(primary, "code", None) if primary is not None else None
    elif isinstance(rhetoric_payload, dict):
        meaning = str(rhetoric_payload.get("intended_meaning") or "").strip()
        hits = rhetoric_payload.get("rhetorics") or []
        primary = next((item for item in hits if item.get("is_primary")), None)
        code = primary.get("code") if isinstance(primary, dict) else None
    else:
        return None
    if not meaning or code == "literal":
        return None
    return meaning


def _check_speech(body: dict) -> dict:
    """ژانر و نیت و بیان را جدا اجرا و با انتظار کاربر می‌سنجد.

    بیان اول تمام می‌شود. ژانر و نیت بعد از آن، با معنای مقصود، هم‌زمان می‌روند.
    """
    text = str(body.get("text") or "").strip()
    started = time.perf_counter()
    rhetoric = {"status": "success", "rhetorics": [], "intended_meaning": ""}
    meaning = None
    if "rhetoric" in _LAYERS:
        rhetoric = _run_traced("rhetoric", text)
        meaning = _meaning_of(rhetoric)
    with ThreadPoolExecutor(max_workers=2) as pool:
        discourse_future = pool.submit(_run_traced, "discourse", text, meaning)
        intent_future = pool.submit(_run_traced, "intent", text, meaning)
        discourse = discourse_future.result()
        intent = intent_future.result()
    wall_ms = round((time.perf_counter() - started) * 1000, 2)
    return combine_check(
        text,
        discourse,
        intent,
        rhetoric,
        body.get("expected_discourse"),
        body.get("expected_intent"),
        body.get("expected_rhetoric"),
        wall_ms,
    )


def _empty_layer(name: str, text: str):
    """خروجی خالی یک لایه را می‌سازد تا بقیهٔ لایه‌ها دور ریخته نشوند."""
    length = len(normalize_text(text))
    if name == "keywords":
        return ExtractKeywordsOutput(
            status="success",
            message="کلمهٔ کلیدی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "topics":
        return ExtractTopicsOutput(
            status="success",
            message="موضوعی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "sentiment":
        return ExtractSentimentOutput(
            status="success",
            message="احساسی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "discourse":
        return ExtractDiscourseOutput(
            status="success",
            message="ژانری استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "intent":
        return ExtractIntentOutput(
            status="success",
            message="نیتی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "rhetoric":
        return ExtractRhetoricOutput(
            status="success",
            message="بیانی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    return ExtractEntitiesOutput(
        status="success",
        message="ذکر موجودیت استخراج نشد",
        source="project_texts",
        table="entity_mentions",
        column="mention_text",
        text_length=length,
        extracted_count=0,
        canonical_count=0,
    )


def _invoke_layer(name: str, text: str, meaning: str | None):
    """یک لایه را اجرا می‌کند. شکست به لایهٔ خالی تبدیل می‌شود."""
    fn = _LAYERS[name]
    try:
        if meaning and name in _MEANING_LAYERS:
            result = fn(text, intended_meaning=meaning)
        else:
            result = fn(text)
    except Exception as exc:
        return name, _empty_layer(name, text), exc
    return name, result, None


def _collect_layers(text: str) -> tuple[dict, dict]:
    """لایه‌های مستقل را هم‌زمان اجرا می‌کند.

    احساس، ژانر و نیت تا تمام شدن بیان صبر می‌کنند و اگر بیان غیرصریح باشد
    همان معنای مقصود را می‌گیرند. شکست یکی بقیه را دور نمی‌ریزد.
    """
    parts: dict = {}
    errors: dict = {}
    free = [name for name in _FREE_LAYERS if name in _LAYERS]
    later = [name for name in _AFTER_RHETORIC if name in _LAYERS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        running = {
            pool.submit(_invoke_layer, name, text, None): name for name in free
        }
        rhetoric_ready = "rhetoric" not in free
        meaning = None
        while running or (later and rhetoric_ready):
            if rhetoric_ready and later:
                for name in later:
                    running[pool.submit(_invoke_layer, name, text, meaning)] = name
                later = []
            if not running:
                break
            done, _pending = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                running.pop(future)
                name, result, exc = future.result()
                parts[name] = result
                if exc is not None:
                    errors[name] = exc
                if name == "rhetoric":
                    meaning = _meaning_of(result)
                    rhetoric_ready = True
    return parts, errors


def _dump_all(text: str) -> dict:
    """هفت لایه را اجرا می‌کند؛ شکست یکی بقیه را دور نمی‌ریزد."""
    parts, errors = _collect_layers(text)
    if len(errors) == len(_LAYERS):
        raise next(iter(errors.values()))
    entities = parts["entities"]
    keywords = drop_entity_copy_keywords(parts["keywords"].keywords, entities.mentions)
    topics = parts["topics"]
    stance = parts["sentiment"]
    discourses = parts["discourse"]
    intents = parts["intent"]
    rhetorics = parts.get("rhetoric") or _empty_layer("rhetoric", text)
    payload = entities.model_dump()
    payload["keywords"] = [item.model_dump() for item in keywords]
    payload["keyword_count"] = len(keywords)
    payload["topics"] = [item.model_dump() for item in topics.topics]
    payload["topic_count"] = topics.topic_count
    payload["sentiment"] = (
        stance.sentiment.model_dump() if stance.sentiment is not None else None
    )
    payload["emotions"] = [item.model_dump() for item in stance.emotions]
    payload["emotion_count"] = stance.emotion_count
    payload["discourses"] = [item.model_dump() for item in discourses.discourses]
    payload["discourse_count"] = discourses.discourse_count
    payload["intents"] = [item.model_dump() for item in intents.intents]
    payload["intent_count"] = intents.intent_count
    payload["rhetorics"] = [item.model_dump() for item in rhetorics.rhetorics]
    payload["rhetoric_count"] = rhetorics.rhetoric_count
    payload["intended_meaning"] = rhetorics.intended_meaning
    payload["normalized_text"] = normalize_text(text)
    payload["layer"] = "all"
    bits = [entities.message]
    if keywords:
        bits.append(parts["keywords"].message)
    if topics.topics:
        bits.append(topics.message)
    if stance.sentiment is not None or stance.emotions:
        bits.append(stance.message)
    if discourses.discourses:
        bits.append(discourses.message)
    if intents.intents:
        bits.append(intents.message)
    if rhetorics.rhetorics:
        bits.append(rhetorics.message)
    for name, exc in errors.items():
        packed = format_error(exc)
        bits.append(
            f"{_LAYER_LABELS[name]} نیامد: {packed.get('message') or 'خطای مدل'}"
        )
    payload["message"] = "؛ ".join(bits)
    payload["layer_errors"] = {
        name: format_error(exc).get("message") for name, exc in errors.items()
    }
    return payload


def _save_extract(body: dict) -> dict:
    """خروجی استخراج را با وضعیت پیشنهادی به CRUD می‌سپارد."""
    from auth.gate import require_permission
    from errors.crud import format_success
    from services.text_analysis import insert_text_analysis

    actor = require_permission("TextAnalysis", "Create")
    fields = {
        "source_type": body.get("source_type") or "content",
        "source_id": body.get("source_id"),
        "text": body.get("text"),
        "mentions": body.get("mentions") or [],
        "keywords": body.get("keywords") or [],
        "topics": body.get("topics") or [],
        "sentiment": body.get("sentiment"),
        "emotions": body.get("emotions") or [],
        "discourses": body.get("discourses") or [],
        "intents": body.get("intents") or [],
        "rhetorics": body.get("rhetorics") or [],
        "intended_meaning": body.get("intended_meaning"),
    }
    if isinstance(body.get("model"), str) and body.get("model").strip():
        fields["model"] = body["model"].strip()
    parsed = _save_input_cls()(**fields).model_dump()
    stored = insert_text_analysis(parsed, created_by=actor["id"])
    packed = format_success("تحلیل متن با وضعیت پیشنهادی ثبت شد", **stored)
    indexed = _try_index(stored["id"])
    if indexed is not None:
        packed["embedding"] = indexed
    return packed


class PlaygroundHandler(BaseHTTPRequestHandler):
    """صفحهٔ استاتیک و API استخراج را پاسخ می‌دهد."""

    server_version = "management-ner-playground/1"

    def log_message(self, format, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _send(
        self,
        status: int,
        body,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        if isinstance(body, (dict, list)):
            payload = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        elif isinstance(body, str):
            payload = body.encode("utf-8")
        else:
            payload = body
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_static(self, relative: str) -> None:
        target = (_STATIC / relative).resolve()
        if not str(target).startswith(str(_STATIC.resolve())) or not target.is_file():
            self._send(404, {"error": "یافت نشد"})
            return
        content_type = _MIME.get(target.suffix, "application/octet-stream")
        self._send(200, target.read_bytes(), content_type)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/check", "/check.html"):
            self._send_static("index.html")
            return
        if path.startswith("/static/"):
            self._send_static(path[len("/static/") :])
            return
        if path == "/api/catalogs":
            self._send(200, catalog_payload())
            return
        if path == "/api/sample":
            self._send(
                200,
                {
                    "text": SAMPLE_TEXT,
                    "note": "متن ساختگی است؛ از دیتابیس نیامده. برای پوشش هر ۹ نوع نوشته شد.",
                },
            )
            return
        self._send(404, {"error": "مسیر پیدا نشد"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = _read_json_body(self)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
            return
        text = body.get("text")
        if not isinstance(text, str) or not text.strip():
            self._send(
                400,
                {"status": "error", "error_code": "INVALID_INPUT", "message": "متن خالی است"},
            )
            return
        if path == "/api/check":
            try:
                self._send(200, _check_speech(body))
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path == "/api/extract":
            try:
                self._send(200, _dump_all(text.strip()))
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path == "/api/save":
            try:
                self._send(200, _save_extract(body))
            except Exception as exc:
                self._send(200, format_crud_error(exc))
            return
        if path.startswith("/api/extract/"):
            layer = path[len("/api/extract/") :]
            if layer not in _LAYERS:
                self._send(404, {"error": "مسیر پیدا نشد"})
                return
            try:
                self._send(
                    200,
                    _dump_layer(
                        layer,
                        text.strip(),
                        intended_meaning=(
                            str(body.get("intended_meaning")).strip()
                            if isinstance(body.get("intended_meaning"), str)
                            else None
                        ),
                    ),
                )
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        self._send(404, {"error": "مسیر پیدا نشد"})


def serve(host: str | None = None, port: int | None = None) -> None:
    """زمین بازی را روی localhost اجرا می‌کند."""
    settings = load_playground_config()
    bind_host = host if host is not None else settings["host"]
    bind_port = port if port is not None else settings["port"]
    setup_logging()
    _save_input_cls()
    actor_label = bind_playground_actor()
    httpd = ThreadingHTTPServer((bind_host, bind_port), PlaygroundHandler)
    url = f"http://{bind_host}:{bind_port}"
    actor_bit = f" · بازیگر {actor_label}" if actor_label else ""
    sys.stderr.write(f"زمین بازی استخراج: {url}{actor_bit}\nقطع با Ctrl+C\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\nزمین بازی بسته شد.\n")
    finally:
        httpd.server_close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="زمین بازی استخراج متن پروژه")
    parser.add_argument("--host", default=None, help="میزبان؛ پیش‌فرض از playground.yaml")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="پورت؛ پیش‌فرض از playground.yaml",
    )
    args = parser.parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
