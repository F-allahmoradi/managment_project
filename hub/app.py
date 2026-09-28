"""سرور HTTP نسخهٔ ۱ برای وب و موبایل.

منطق هر جدول در همان ابزار MCP می‌ماند. این فایل فقط ورود،
CORS، و ترجمهٔ درخواست HTTP به همان ابزار است.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import base64
import json
import logging
from pathlib import Path
import tempfile

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from hub.bootstrap import install_hub_import_path

install_hub_import_path()

from auth.http import (
    DOMAIN_UNAVAILABLE,
    INVALID_INPUT,
    METHOD_NOT_ALLOWED,
    PAYLOAD_TOO_LARGE,
    UNAUTHENTICATED,
    UNKNOWN_DOMAIN,
    UNKNOWN_TOOL,
    error_body,
    extract_bearer,
    http_status_for,
)
from auth.sessions import (
    AuthError,
    authenticate,
    ensure_api_sessions,
    issue_session,
    register_account,
    revoke_token,
    user_for_token,
)
from hub.config import load_settings
from hub.analysis import (
    analyze_source,
    commit_analysis,
    get_preview_job,
    start_preview_job,
)
from hub.pool import DomainPool, WorkerError
from hub.uploads import store_upload
from hub.registry import DASHBOARD_ROUTES, merge_route_arguments
from hub.spec import build_openapi

LOGGER = logging.getLogger("hub")
_DOCS_PATH = Path(__file__).resolve().parent / "static" / "index.html"
_LOGIN_WINDOW = timedelta(minutes=5)
_LOGIN_LIMIT = 8


class Json(JSONResponse):
    """JSON فارسی را بدون escape اضافه برمی‌گرداند."""

    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False, default=str).encode("utf-8")


def create_app(settings: dict | None = None) -> CORSMiddleware:
    """اپ ASGI را با CORS می‌سازد. فرآیند دامنه‌ها در lifespan بالا می‌آید."""
    chosen = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: Starlette):
        app.state.settings = chosen
        app.state.login_failures = {}
        app.state.register_attempts = {}
        pool = DomainPool(tuple(chosen["domains"]), chosen["tool_timeout_seconds"])
        await run_in_threadpool(pool.start)
        app.state.pool = pool
        app.state.db_ready = True
        app.state.db_message = None
        try:
            await run_in_threadpool(ensure_api_sessions)
        except Exception:
            LOGGER.exception("جدول نشست ساخته نشد")
            app.state.db_ready = False
            app.state.db_message = "اتصال پایگاه برای ورود آماده نیست"
        try:
            yield
        finally:
            await run_in_threadpool(pool.stop)

    routes = [
        Route("/api/v1", root, methods=["GET"]),
        Route("/api/v1/health", health, methods=["GET"]),
        Route("/api/v1/docs", docs, methods=["GET"]),
        Route("/api/v1/openapi.json", openapi, methods=["GET"]),
        Route("/api/v1/catalog", catalog, methods=["GET"]),
        Route("/api/v1/auth/login", login, methods=["POST"]),
        Route("/api/v1/auth/register", register, methods=["POST"]),
        Route("/api/v1/auth/logout", logout, methods=["POST"]),
        Route("/api/v1/auth/me", me, methods=["GET"]),
        Route("/api/v1/stt/transcribe", transcribe_speech, methods=["POST"]),
        Route("/api/v1/stt/save", save_speech, methods=["POST"]),
        Route("/api/v1/media/save", save_media, methods=["POST"]),
        Route("/api/v1/text-analyses/preview/{job_id}", poll_extracted_analysis, methods=["GET"]),
        Route("/api/v1/text-analyses/preview", preview_extracted_analysis, methods=["POST"]),
        Route("/api/v1/text-analyses/commit", commit_extracted_analysis, methods=["POST"]),
        Route("/api/v1/text-analyses", save_extracted_analysis, methods=["POST"]),
        Route("/api/v1/{domain}/tools/{tool_name}", call_tool, methods=["GET", "POST"]),
    ]
    for route in DASHBOARD_ROUTES:
        routes.append(
            Route(
                route["path"],
                _dashboard_endpoint(route),
                methods=[route["method"]],
                name=f"{route['method'].lower()} {route['path']}",
            )
        )
    inner = Starlette(routes=routes, lifespan=lifespan)
    origins = list(chosen["cors_origins"])
    for extra in ("https://localhost", "http://localhost", "capacitor://localhost"):
        if extra not in origins:
            origins.append(extra)
    return CORSMiddleware(
        inner,
        allow_origins=origins,
        allow_origin_regex=r"https?://localhost(:\d+)?",
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )


async def root(_: Request) -> Json:
    return Json({
        "status": "success",
        "name": "management-api",
        "version": "1",
        "health": "/api/v1/health",
        "docs": "/api/v1/docs",
        "catalog": "/api/v1/catalog",
        "openapi": "/api/v1/openapi.json",
    })


async def health(request: Request) -> Json:
    pool = _pool(request)
    domains = pool.status() if pool is not None else []
    ready = any(item["ready"] for item in domains)
    payload = {
        "status": "success" if ready else "error",
        "message": "سرویس API آماده است" if ready else "هیچ دامنه‌ای بالا نیامد",
        "database": bool(request.app.state.db_ready),
        "database_message": request.app.state.db_message,
        "domains": domains,
    }
    if not ready:
        payload["error_code"] = DOMAIN_UNAVAILABLE
    return Json(payload, status_code=200 if ready else 503)


async def docs(_: Request) -> HTMLResponse:
    if not _DOCS_PATH.is_file():
        return HTMLResponse("راهنما پیدا نشد", status_code=404)
    return HTMLResponse(_DOCS_PATH.read_text(encoding="utf-8"))


async def openapi(request: Request) -> Json:
    pool = _pool(request)
    catalog_groups = pool.catalog() if pool is not None else []
    return Json(build_openapi(catalog_groups))


async def catalog(request: Request) -> Json:
    pool = _pool(request)
    return Json({
        "status": "success",
        "message": "کاتالوگ API",
        "routes": [
            {"method": item["method"], "path": item["path"], "domain": item["domain"], "tool": item["tool"]}
            for item in DASHBOARD_ROUTES
        ],
        "domains": pool.catalog() if pool is not None else [],
    })


async def login(request: Request) -> Json:
    if not request.app.state.db_ready:
        return _error(DOMAIN_UNAVAILABLE, "ورود فعلاً به پایگاه وصل نیست")
    limited = _too_many_logins(request)
    if limited is not None:
        return limited
    payload = await _json_object(request)
    if isinstance(payload, Json):
        return payload
    try:
        user = await run_in_threadpool(
            authenticate,
            str(payload.get("username") or ""),
            str(payload.get("password") or ""),
        )
        session = await run_in_threadpool(
            issue_session,
            user["id"],
            request.app.state.settings["session_ttl_hours"],
        )
    except AuthError as exc:
        _record_login_failure(request)
        return _error(exc.error_code, exc.message)
    except Exception:
        LOGGER.exception("ورود ناموفق بود")
        return _error("DATABASE_ERROR", "ورود انجام نشد")
    _clear_login_failures(request)
    return Json({
        "status": "success",
        "message": "ورود انجام شد",
        "user": user,
        **session,
    })


async def register(request: Request) -> Json:
    if not request.app.state.db_ready:
        return _error(DOMAIN_UNAVAILABLE, "ثبت‌نام فعلاً به پایگاه وصل نیست")
    limited = _too_many_registers(request)
    if limited is not None:
        return limited
    payload = await _json_object(request)
    if isinstance(payload, Json):
        return payload
    try:
        user = await run_in_threadpool(register_account, payload)
        session = await run_in_threadpool(
            issue_session,
            user["id"],
            request.app.state.settings["session_ttl_hours"],
        )
    except AuthError as exc:
        return _error(exc.error_code, exc.message)
    except Exception:
        LOGGER.exception("ثبت‌نام ناموفق بود")
        return _error("DATABASE_ERROR", "ثبت‌نام انجام نشد")
    return Json({
        "status": "success",
        "message": "ثبت‌نام انجام شد",
        "user": user,
        **session,
    })


async def logout(request: Request) -> Json:
    user, token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    await run_in_threadpool(revoke_token, token)
    return Json({"status": "success", "message": "خروج انجام شد", "user": user})


async def me(request: Request) -> Json:
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    return Json({"status": "success", "message": "کاربر جاری", "user": user})


_AUDIO_SUFFIX = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/3gpp": ".3gp",
    "audio/amr": ".amr",
}


async def transcribe_speech(request: Request) -> Json:
    """مرحلهٔ ۲: فایل ضبط‌شده را می‌گیرد و متن فارسی برمی‌گرداند."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    if "stt" not in request.app.state.settings["domains"]:
        return _error(DOMAIN_UNAVAILABLE, "تبدیل گفتار روی این سرور فعال نیست")
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type in {"application/json", "text/json"}:
        payload = await _json_object(request)
        if isinstance(payload, Json):
            return payload
        raw = str(payload.get("audio_base64") or payload.get("data") or "").strip()
        if not raw:
            return _error(INVALID_INPUT, "فایل صوتی خالی است")
        try:
            body = base64.b64decode(raw)
        except (ValueError, TypeError):
            return _error(INVALID_INPUT, "فایل صوتی نامعتبر است")
        content_type = str(payload.get("mime_type") or "audio/webm").split(";")[0].strip().lower()
    else:
        body = await request.body()
        if not content_type:
            content_type = "audio/webm"
    limit = request.app.state.settings["max_body_bytes"]
    if not body:
        return _error(INVALID_INPUT, "فایل صوتی خالی است")
    if len(body) > limit:
        return _error(PAYLOAD_TOO_LARGE, "حجم صدا از حد مجاز بیشتر است")
    suffix = _AUDIO_SUFFIX.get(content_type, ".webm")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(body)
            temp_path = tmp.name
        return await _invoke(
            request,
            "stt",
            "transcribe_audio",
            {"file_path": temp_path, "language": "fa-IR"},
        )
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


async def save_speech(request: Request) -> Json:
    """متن را ذخیره می‌کند و اگر فایل بیاید خود صوت را هم نگه می‌دارد."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    if "stt" not in request.app.state.settings["domains"]:
        return _error(DOMAIN_UNAVAILABLE, "تبدیل گفتار روی این سرور فعال نیست")
    form = await request.form()
    text = str(form.get("text") or "").strip()
    if not text:
        return _error(INVALID_INPUT, "متن رونویسی لازم است")
    upload = form.get("file")
    temp_path = None
    arguments = {"text": text}
    try:
        if upload is not None and hasattr(upload, "read"):
            body = await upload.read()
            limit = request.app.state.settings["max_body_bytes"]
            if not body:
                return _error(INVALID_INPUT, "فایل صوتی خالی است")
            if len(body) > limit:
                return _error(PAYLOAD_TOO_LARGE, "حجم صدا از حد مجاز بیشتر است")
            content_type = (getattr(upload, "content_type", None) or "audio/webm").split(";")[0].strip().lower()
            suffix = _AUDIO_SUFFIX.get(content_type, ".webm")
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(body)
                temp_path = tmp.name
            arguments["file_path"] = temp_path
            arguments["mime_type"] = content_type
            arguments["original_filename"] = getattr(upload, "filename", None) or ("voice" + suffix)
        return await _invoke(request, "stt", "save_transcript", arguments)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


async def save_media(request: Request) -> Json:
    """عکس، فیلم یا سند را روی دیسک می‌نویسد و در contents ثبت می‌کند."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    if "crud" not in request.app.state.settings["domains"]:
        return _error(DOMAIN_UNAVAILABLE, "ثبت فایل روی این سرور فعال نیست")
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "read"):
        return _error(INVALID_INPUT, "فایل لازم است")
    body = await upload.read()
    limit = request.app.state.settings["max_body_bytes"]
    if not body:
        return _error(INVALID_INPUT, "فایل خالی است")
    if len(body) > limit:
        return _error(PAYLOAD_TOO_LARGE, "حجم فایل از حد مجاز بیشتر است")
    stored = None
    try:
        stored = store_upload(
            body,
            int(user["id"]),
            getattr(upload, "content_type", None) or "",
            getattr(upload, "filename", None) or "",
        )
    except ValueError as exc:
        return _error(INVALID_INPUT, str(exc))
    arguments = {
        "content_kind": stored["content_kind"],
        "storage_key": stored["storage_key"],
        "original_filename": stored["original_filename"],
        "mime_type": stored["mime_type"],
        "file_size_bytes": stored["file_size_bytes"],
    }
    try:
        result = await _invoke(request, "crud", "create_content", arguments)
    except Exception:
        Path(stored["path"]).unlink(missing_ok=True)
        raise
    if result.status_code >= 400:
        Path(stored["path"]).unlink(missing_ok=True)
    return result


async def _analysis_source(request: Request):
    """نوع و شناسه منبع را از بدنه می‌خواند."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return None, None, None, failure
    payload = await _json_object(request)
    if isinstance(payload, Json):
        return None, None, None, payload
    source_type = str(payload.get("source_type") or "").strip()
    try:
        source_id = int(payload.get("source_id") or 0)
    except (TypeError, ValueError):
        return None, None, None, _error(INVALID_INPUT, "شناسه منبع نامعتبر است")
    if source_id < 1:
        return None, None, None, _error(INVALID_INPUT, "شناسه منبع لازم است")
    return user, source_type, source_id, None


async def preview_extracted_analysis(request: Request) -> Json:
    """استخراج را شروع می‌کند و پیشرفت لایه‌ها را برای پولینگ برمی‌گرداند."""
    user, source_type, source_id, failure = await _analysis_source(request)
    if failure is not None:
        return failure
    pool = _pool(request)
    if pool is None:
        return _error(DOMAIN_UNAVAILABLE, "سرویس دامنه بالا نیست")
    result = await run_in_threadpool(
        start_preview_job,
        pool,
        tuple(request.app.state.settings["domains"]),
        user["id"],
        source_type,
        source_id,
    )
    return Json(result, status_code=http_status_for(result))


async def poll_extracted_analysis(request: Request) -> Json:
    """وضعیت یک استخراج در جریان را می‌خواند."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    job_id = str(request.path_params.get("job_id") or "").strip()
    result = get_preview_job(job_id, user["id"])
    return Json(result, status_code=http_status_for(result))


async def commit_extracted_analysis(request: Request) -> Json:
    """موارد استخراج‌شدهٔ تأییدشده را در پایگاه می‌نویسد."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    payload = await _json_object(request)
    if isinstance(payload, Json):
        return payload
    fields = payload.get("fields")
    if not isinstance(fields, dict):
        return _error(INVALID_INPUT, "موارد استخراج لازم است")
    pool = _pool(request)
    if pool is None:
        return _error(DOMAIN_UNAVAILABLE, "سرویس دامنه بالا نیست")
    result = await run_in_threadpool(
        commit_analysis,
        pool,
        tuple(request.app.state.settings["domains"]),
        user["id"],
        fields,
    )
    return Json(result, status_code=http_status_for(result))


async def save_extracted_analysis(request: Request) -> Json:
    """متن ذخیره‌شده را استخراج می‌کند و تحلیل پیشنهادی می‌نویسد."""
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    payload = await _json_object(request)
    if isinstance(payload, Json):
        return payload
    source_type = str(payload.get("source_type") or "").strip()
    try:
        source_id = int(payload.get("source_id") or 0)
    except (TypeError, ValueError):
        return _error(INVALID_INPUT, "شناسه منبع نامعتبر است")
    if source_id < 1:
        return _error(INVALID_INPUT, "شناسه منبع لازم است")
    pool = _pool(request)
    if pool is None:
        return _error(DOMAIN_UNAVAILABLE, "سرویس دامنه بالا نیست")
    result = await run_in_threadpool(
        analyze_source,
        pool,
        tuple(request.app.state.settings["domains"]),
        user["id"],
        source_type,
        source_id,
    )
    status = http_status_for(result)
    return Json(result, status_code=status)


async def call_tool(request: Request) -> Json:
    domain = request.path_params["domain"]
    tool_name = request.path_params["tool_name"]
    pool = _pool(request)
    if pool is None or domain not in request.app.state.settings["domains"]:
        return _error(UNKNOWN_DOMAIN, f"دامنه {domain} در این API نیست")
    info = pool.tool_info(domain, tool_name)
    if info is None:
        return _error(UNKNOWN_TOOL, f"ابزار {tool_name} در دامنه {domain} نیست")
    if request.method == "GET" and not info.get("read_only"):
        return _error(METHOD_NOT_ALLOWED, "این ابزار فقط با POST صدا زده می‌شود")
    arguments = await _arguments(request)
    if isinstance(arguments, Json):
        return arguments
    return await _invoke(request, domain, tool_name, arguments)


def _dashboard_endpoint(route: dict):
    async def endpoint(request: Request) -> Json:
        arguments = await _arguments(request)
        if isinstance(arguments, Json):
            return arguments
        try:
            arguments = merge_route_arguments(route, request.path_params, arguments)
        except (TypeError, ValueError):
            return _error(INVALID_INPUT, "شناسه مسیر نامعتبر است")
        return await _invoke(request, route["domain"], route["tool"], arguments)

    return endpoint


async def _invoke(request: Request, domain: str, tool: str, arguments: dict) -> Json:
    user, _token, failure = await _user_from_request(request)
    if failure is not None:
        return failure
    pool = _pool(request)
    if pool is None:
        return _error(DOMAIN_UNAVAILABLE, "سرویس دامنه بالا نیست")
    try:
        result = await run_in_threadpool(pool.call, domain, tool, arguments, user["id"])
    except WorkerError as exc:
        return _error(exc.error_code, exc.message)
    status = http_status_for(result)
    return Json(result, status_code=status)


async def _user_from_request(request: Request):
    if not request.app.state.db_ready:
        return None, None, _error(DOMAIN_UNAVAILABLE, "نشست به پایگاه وصل نیست")
    token = extract_bearer(request.headers.get("authorization"))
    if not token:
        return None, None, _error(UNAUTHENTICATED, "توکن Bearer لازم است")
    try:
        user = await run_in_threadpool(user_for_token, token)
    except Exception:
        LOGGER.exception("خواندن نشست ناموفق بود")
        return None, None, _error("DATABASE_ERROR", "نشست خوانده نشد")
    if user is None:
        return None, None, _error(UNAUTHENTICATED, "توکن نامعتبر یا منقضی است")
    return user, token, None


async def _arguments(request: Request):
    if request.method == "GET":
        return {key: value for key, value in request.query_params.items()}
    return await _json_object(request)


async def _json_object(request: Request):
    body = await request.body()
    limit = request.app.state.settings["max_body_bytes"]
    if len(body) > limit:
        return _error(PAYLOAD_TOO_LARGE, "حجم بدنه از حد مجاز بیشتر است")
    if not body:
        return {}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return _error(INVALID_INPUT, "بدنه باید JSON باشد")
    if not isinstance(payload, dict):
        return _error(INVALID_INPUT, "بدنه باید یک شیء JSON باشد")
    return payload


def _pool(request: Request):
    return getattr(request.app.state, "pool", None)


def _error(error_code: str, message: str) -> Json:
    payload = error_body(error_code, message)
    return Json(payload, status_code=http_status_for(payload))


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host


def _too_many_logins(request: Request):
    now = datetime.utcnow()
    recent = [
        moment
        for moment in request.app.state.login_failures.get(_client_key(request), [])
        if now - moment < _LOGIN_WINDOW
    ]
    request.app.state.login_failures[_client_key(request)] = recent
    if len(recent) >= _LOGIN_LIMIT:
        return Json(
            error_body(UNAUTHENTICATED, "تلاش ورود بیش از حد است؛ چند دقیقه بعد دوباره تلاش کنید"),
            status_code=429,
        )
    return None


def _record_login_failure(request: Request) -> None:
    key = _client_key(request)
    request.app.state.login_failures.setdefault(key, []).append(datetime.utcnow())


def _clear_login_failures(request: Request) -> None:
    request.app.state.login_failures.pop(_client_key(request), None)


def _too_many_registers(request: Request):
    now = datetime.utcnow()
    key = _client_key(request)
    recent = [
        moment
        for moment in request.app.state.register_attempts.get(key, [])
        if now - moment < _LOGIN_WINDOW
    ]
    recent.append(now)
    request.app.state.register_attempts[key] = recent
    if len(recent) > _LOGIN_LIMIT:
        return Json(
            error_body(UNAUTHENTICATED, "تلاش ثبت‌نام بیش از حد است؛ چند دقیقه بعد دوباره تلاش کنید"),
            status_code=429,
        )
    return None


app = create_app()
