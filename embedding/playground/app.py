"""سرور HTTP محلی برای تست MCPها روی یک صفحه.

هر بخش یک سرور است، نه یک tool. stdio مخصوص کلاینت MCP می‌ماند.
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import sys
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from auth.gate import require_permission
from business_logic.config import load_llm_public
from business_logic.indexer import index_analysis, index_pending
from business_logic.repository import fetch_embedding_summaries
from business_logic.searcher import search_similar
from errors.crud import format_error, format_success
from logging_module import setup_logging
from playground.config import bind_playground_actor, load_playground_config
from playground.hub import (
    catalog,
    extract_nlp,
    extract_text,
    load_nlp_sample,
    load_sample,
    load_search_samples,
    snapshot,
)
from services.text_analysis import fetch_text_analyses_for_actor
from validators.search import validate_search_similar

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


def _list_analyses() -> dict:
    """تحلیل‌های بازیگر جاری را با وضعیت بردار همین مدل فهرست می‌کند."""
    actor = require_permission("TextAnalysis", "Read")
    records = fetch_text_analyses_for_actor(actor["id"], 20, 0)
    model = str(load_llm_public().get("embedding_model") or "text-embedding-3-small").strip()
    summaries = {
        item["analysis_id"]: item
        for item in fetch_embedding_summaries([row["id"] for row in records], model)
    }
    packed = []
    for row in records:
        summary = summaries.get(row["id"]) or {}
        packed.append(
            {
                **row,
                "embedding": {
                    "indexed": bool(summary.get("card_count")),
                    "model": model,
                    "card_count": int(summary.get("card_count") or 0),
                    "raw_count": int(summary.get("raw_count") or 0),
                    "entity_count": int(summary.get("entity_count") or 0),
                    "intent_count": int(summary.get("intent_count") or 0),
                    "intent_slot_count": int(summary.get("intent_slot_count") or 0),
                },
            }
        )
    return format_success("تحلیل‌ها فهرست شدند", records=packed, model=model)


def _index_one(body: dict) -> dict:
    """یک تحلیل را امبد می‌کند."""
    actor = require_permission("TextAnalysis", "Create")
    analysis_id = int(body.get("analysis_id") or 0)
    stored = index_analysis(analysis_id, actor["id"])
    return format_success("تحلیل متن برداری شد", **stored)


def _index_left(body: dict) -> dict:
    """تحلیل‌های بدون بردار را امبد می‌کند."""
    actor = require_permission("TextAnalysis", "Create")
    limit = int(body.get("limit") or 20)
    stored = index_pending(actor["id"], limit)
    return format_success("تحلیل‌های باقی‌مانده برداری شدند", **stored)


def _search(body: dict) -> dict:
    """سؤال را معنایی جستجو می‌کند."""
    actor = require_permission("TextAnalysis", "Read")
    parsed = validate_search_similar(
        query=str(body.get("query") or ""),
        kinds=body.get("kinds"),
        source_type=body.get("source_type") or None,
        limit=int(body.get("limit") or 8),
    )
    found = search_similar(
        actor["id"],
        parsed["query"],
        kinds=parsed.get("kinds"),
        source_type=parsed.get("source_type"),
        limit=parsed["limit"],
    )
    return format_success("موارد مشابه پیدا شد", **found)


class PlaygroundHandler(BaseHTTPRequestHandler):
    """صفحهٔ استاتیک و API زمین بازی MCP را پاسخ می‌دهد."""

    server_version = "management-playground/1"

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
        if path == "/":
            self._send_static("index.html")
            return
        if path.startswith("/static/"):
            self._send_static(path[len("/static/") :])
            return
        if path == "/api/hub":
            self._send(200, catalog())
            return
        if path == "/api/search-samples":
            self._send(200, load_search_samples())
            return
        if path == "/api/analyses":
            try:
                self._send(200, _list_analyses())
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path == "/api/mcp/ner/sample":
            try:
                self._send(200, load_sample())
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path == "/api/mcp/nlp/sample":
            try:
                self._send(200, load_nlp_sample())
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path.startswith("/api/mcp/"):
            mcp_id = path[len("/api/mcp/") :]
            try:
                self._send(200, snapshot(mcp_id))
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        self._send(404, {"error": "مسیر پیدا نشد"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = _read_json_body(self)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
            return
        if path in ("/api/mcp/ner/extract", "/api/mcp/nlp/extract"):
            text = body.get("text")
            if not isinstance(text, str) or not text.strip():
                self._send(
                    400,
                    {
                        "status": "error",
                        "error_code": "INVALID_INPUT",
                        "message": "متن خالی است",
                    },
                )
                return
            runner = extract_nlp if path.endswith("/nlp/extract") else extract_text
            try:
                self._send(200, runner(text.strip()))
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        handlers = {
            "/api/index": _index_one,
            "/api/index-pending": _index_left,
            "/api/search": _search,
        }
        handler = handlers.get(path)
        if handler is None:
            self._send(404, {"error": "مسیر پیدا نشد"})
            return
        try:
            self._send(200, handler(body))
        except Exception as exc:
            self._send(200, format_error(exc))


def serve(host: str | None = None, port: int | None = None) -> None:
    """زمین بازی را روی localhost اجرا می‌کند."""
    settings = load_playground_config()
    bind_host = host if host is not None else settings["host"]
    bind_port = port if port is not None else settings["port"]
    setup_logging()
    actor_label = bind_playground_actor()
    httpd = ThreadingHTTPServer((bind_host, bind_port), PlaygroundHandler)
    url = f"http://{bind_host}:{bind_port}"
    actor_bit = f" · بازیگر {actor_label}" if actor_label else ""
    sys.stderr.write(f"زمین بازی MCP: {url}{actor_bit}\nقطع با Ctrl+C\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\nزمین بازی بسته شد.\n")
    finally:
        httpd.server_close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="زمین بازی یک‌صفحه‌ای MCPها")
    parser.add_argument("--host", default=None, help="میزبان؛ پیش‌فرض از playground.yaml")
    parser.add_argument("--port", type=int, default=None, help="پورت؛ پیش‌فرض ۸۷۷۹")
    args = parser.parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
