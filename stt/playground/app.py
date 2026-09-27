"""سرور HTTP محلی برای ضبط مرورگر، تبدیل به متن، و ذخیره صوت+متن.

stdio مخصوص کلاینت MCP می‌ماند. اینجا فقط localhost است.
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import cgi
import json
import sys
import tempfile
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path, load_crud_symbol

ensure_import_path()

from business_logic.store import resolve_media_path
from business_logic.transcribe import save_voice_and_transcript, transcribe_file
from errors.crud import format_error, format_success
from logging_module import setup_logging
from mcp_server.tools.delete_transcript import run_delete_transcript
from mcp_server.tools.save_transcript import run_save_transcript
from playground.config import bind_playground_actor, load_playground_config

_STATIC = Path(__file__).resolve().parent / "static"
_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}
_MAX_AUDIO = 20_000_000
_SUFFIX = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
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


def _read_audio_body(handler: BaseHTTPRequestHandler) -> tuple[bytes, str]:
    """بدنه باینری صوت را می‌خواند."""
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        raise ValueError("فایل صوتی خالی است")
    if length > _MAX_AUDIO:
        raise ValueError("فایل صوتی بزرگ‌تر از حد مجاز است")
    data = handler.rfile.read(length)
    content_type = (handler.headers.get("Content-Type") or "audio/webm").split(";")[0].strip()
    return data, content_type


def _read_save_form(handler: BaseHTTPRequestHandler) -> dict:
    """متن و فایل صوت را از multipart یا JSON می‌خواند."""
    content_type = handler.headers.get("Content-Type") or ""
    if content_type.startswith("multipart/form-data"):
        form = cgi.FieldStorage(
            fp=handler.rfile,
            headers=handler.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": handler.headers.get("Content-Length") or "0",
            },
        )
        text = form.getfirst("text") or ""
        audio_item = form["audio"] if "audio" in form else None
        audio_bytes = b""
        mime_type = "audio/webm"
        filename = "recording.webm"
        if audio_item is not None and getattr(audio_item, "file", None):
            audio_bytes = audio_item.file.read(_MAX_AUDIO + 1)
            if len(audio_bytes) > _MAX_AUDIO:
                raise ValueError("فایل صوتی بزرگ‌تر از حد مجاز است")
            mime_type = audio_item.type or "audio/webm"
            filename = Path(audio_item.filename or filename).name
        return {
            "text": text,
            "audio_bytes": audio_bytes,
            "mime_type": mime_type,
            "original_filename": filename,
        }
    body = _read_json_body(handler)
    return {
        "text": body.get("text") or "",
        "audio_bytes": b"",
        "mime_type": "audio/webm",
        "original_filename": "recording.webm",
    }


class Handler(BaseHTTPRequestHandler):
    """مسیرهای استاتیک، رونویسی، ذخیره صوت+متن، و پخش فایل."""

    def log_message(self, format, *args):
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> dict:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, raw, "application/json; charset=utf-8")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/audio/"):
            try:
                content_id = int(parsed.path.rsplit("/", 1)[-1])
                fetch_content = load_crud_symbol("services.content", "fetch_content")
                row = fetch_content(content_id)
                if not row.get("storage_key"):
                    raise ValueError("این محتوا فایل صوت ندارد")
                path = resolve_media_path(row["storage_key"])
                mime = row.get("mime_type") or "application/octet-stream"
                self._send(200, path.read_bytes(), mime)
            except Exception as exc:
                self._send_json(400, format_error(exc))
            return
        if parsed.path in ("/", "/index.html"):
            name = "index.html"
        elif parsed.path.startswith("/static/"):
            name = parsed.path[len("/static/") :]
        else:
            self._send(404, b"not found", "text/plain")
            return
        target = (_STATIC / name).resolve()
        if _STATIC.resolve() not in target.parents and target != (_STATIC / "index.html").resolve():
            self._send(404, b"not found", "text/plain")
            return
        if not target.is_file():
            self._send(404, b"not found", "text/plain")
            return
        content_type = _MIME.get(target.suffix, "application/octet-stream")
        self._send(200, target.read_bytes(), content_type)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/transcribe":
                data, content_type = _read_audio_body(self)
                suffix = _SUFFIX.get(content_type, ".webm")
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(data)
                        temp_path = tmp.name
                    text = transcribe_file(temp_path, language="fa-IR")
                    self._send_json(200, format_success("صدا به متن تبدیل شد", transcribed_text=text))
                finally:
                    if temp_path:
                        Path(temp_path).unlink(missing_ok=True)
                return
            if parsed.path == "/api/save":
                from auth.gate import require_permission

                form = _read_save_form(self)
                actor = require_permission("Content", "Create")
                if form["audio_bytes"]:
                    new_id = save_voice_and_transcript(
                        form["text"],
                        form["audio_bytes"],
                        created_by=actor["id"],
                        mime_type=form["mime_type"],
                        original_filename=form["original_filename"],
                    )
                    self._send_json(
                        200,
                        format_success(
                            "متن و فایل صوت ذخیره شد",
                            id=new_id,
                            content_kind="VOICE",
                        ),
                    )
                    return
                result = run_save_transcript(text=form["text"])
                status = 200 if result.get("status") == "success" else 400
                self._send_json(status, result)
                return
            if parsed.path == "/api/delete":
                body = _read_json_body(self)
                result = run_delete_transcript(id=int(body.get("id") or 0))
                status = 200 if result.get("status") == "success" else 400
                self._send_json(status, result)
                return
            if parsed.path == "/api/recent":
                from auth.gate import require_permission

                fetch_contents_for_actor = load_crud_symbol(
                    "services.content",
                    "fetch_contents_for_actor",
                )
                actor = require_permission("Content", "Read")
                records = fetch_contents_for_actor(actor["id"], 10, 0)
                self._send_json(200, format_success("محتواها فهرست شدند", records=records))
                return
        except Exception as exc:
            self._send_json(400, format_error(exc))
            return
        self._send(404, b"not found", "text/plain")


def main() -> None:
    """زمین بازی STT را روی localhost اجرا می‌کند."""
    setup_logging()
    bind_playground_actor()
    settings = load_playground_config()
    host = settings["host"]
    port = settings["port"]
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"STT playground http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
