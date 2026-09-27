"""ثبت شروع، مراحل، و مدت هر عملیات MCP.

هر ابزار یک عملیات است. مراحل تو در تو با duration_ms جدا لاگ می‌شوند.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import functools
import time
import uuid

from logging_module.config import load_logging_config
from logging_module.setup import get_logger

_current_operation: ContextVar["Operation | None"] = ContextVar(
    "mcp_current_operation",
    default=None,
)

_SAFE_COUNT_KEYS = (
    "extracted_count",
    "text_length",
    "n",
    "total",
    "count",
    "page",
    "page_size",
    "people_count",
    "date_count",
    "project_count",
    "action_count",
    "decision_count",
    "task_count",
    "suggestion_count",
    "canonical_count",
    "mention_count",
    "topic_count",
    "keyword_count",
    "emotion_count",
    "discourse_count",
    "intent_count",
)


def _ms(started: float) -> float:
    """مدت از started را به میلی‌ثانیه گرد می‌کند."""
    return round((time.perf_counter() - started) * 1000, 2)


def _payload_of(result):
    """خروجی مرحله را اگر مدل Pydantic باشد به دیکشنری تبدیل می‌کند."""
    if isinstance(result, (list, tuple, dict, int, float, bool, str, type(None))):
        return result
    dump = getattr(result, "model_dump", None)
    if callable(dump):
        try:
            return dump()
        except Exception:
            return result
    return result


def _extra_from_result(result, step_name: str | None = None) -> dict:
    """از خروجی مرحله فقط اندازه یا شمار را برمی‌دارد، نه مقدارهای دامنه.

    ورودی:
        result: برگشتی تابع مرحله.
        step_name: برچسب مرحله تا عدد خام insert با دادهٔ حساس قاطی نشود.
    خروجی:
        دیکشنری کوچک برای لاگ؛ ممکن است خالی باشد.
    علت:
        نام و رمز اتصال نباید در لاگ بیایند.
        شناسهٔ ردیف بعد از insert برای ردگیری لازم است.
    """
    extra: dict = {}
    payload = _payload_of(result)
    if isinstance(payload, (list, tuple)):
        extra["count"] = len(payload)
    elif isinstance(payload, dict):
        extra["keys"] = len(payload)
        value = payload.get("id")
        if isinstance(value, int) and not isinstance(value, bool):
            extra["id"] = value
        for key in _SAFE_COUNT_KEYS:
            value = payload.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                extra[key] = value
        missing = payload.get("missing_fields")
        if isinstance(missing, list):
            extra["missing_count"] = len(missing)
        entities = payload.get("entities")
        if isinstance(entities, list):
            extra["entity_count"] = len(entities)
    elif isinstance(payload, int) and not isinstance(payload, bool):
        if step_name in ("insert", "update", "delete"):
            extra["id"] = payload
        elif step_name in ("count_null", "paginate"):
            extra["count"] = payload
    return extra


def _format_fields(fields: dict) -> str:
    """دیکشنری را به key=value برای یک خط لاگ تبدیل می‌کند."""
    parts = []
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        parts.append(f"{key}={value}")
    return " ".join(parts)


@dataclass
class StepRecord:
    """یک مرحلهٔ داخل عملیات ابزار."""

    name: str
    detail: str
    status: str = "success"
    duration_ms: float = 0.0
    seq: int = 0
    depth: int = 0
    parent: str | None = None
    path: str = ""
    module: str | None = None
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        """همان مرحله را برای JSON پاسخ و تست برمی‌گرداند."""
        payload = {
            "name": self.name,
            "detail": self.detail,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "seq": self.seq,
            "depth": self.depth,
            "path": self.path,
        }
        if self.parent:
            payload["parent"] = self.parent
        if self.module:
            payload["module"] = self.module
        payload.update(self.extra)
        return payload


@dataclass
class Operation:
    """یک فراخوانی ابزار یا منبع یا پرامپت MCP."""

    kind: str
    name: str
    op_id: str
    started: float
    status: str = "success"
    error_code: str | None = None
    error_type: str | None = None
    steps: list[StepRecord] = field(default_factory=list)
    _stack: list[str] = field(default_factory=list)
    _seq: int = 0

    def enter_step(self, name: str) -> tuple[int, int, str | None, str]:
        """شماره و عمق و والد و مسیر مرحلهٔ جدید را برمی‌گرداند."""
        self._seq += 1
        parent = self._stack[-1] if self._stack else None
        depth = len(self._stack)
        path = "/".join([*self._stack, name])
        self._stack.append(name)
        return self._seq, depth, parent, path

    def leave_step(self) -> None:
        """مرحلهٔ جاری را از پشتهٔ زنجیره برمی‌دارد."""
        if self._stack:
            self._stack.pop()

    def chain(self) -> str:
        """ترتیب اتمام مراحل را با کاما برمی‌گرداند."""
        return ",".join(step.name for step in self.steps)

    def slowest(self) -> StepRecord | None:
        """کندترین مرحله را برمی‌گرداند؛ اگر مرحله‌ای نباشد None."""
        if not self.steps:
            return None
        return max(self.steps, key=lambda step: step.duration_ms)

    def snapshot(self) -> dict:
        """وضعیت فعلی عملیات را با مدت تا همین لحظه برمی‌گرداند.

        ورودی:
            هیچ.
        خروجی:
            دیکشنری trace شامل name، status، duration_ms، chain و steps.
        علت:
            کلاینت MCP باید مراحل و زمان و جای زنجیره را در همان پاسخ ببیند.
        """
        payload = {
            "kind": self.kind,
            "name": self.name,
            "op_id": self.op_id,
            "status": self.status,
            "duration_ms": _ms(self.started),
            "step_count": len(self.steps),
            "chain": self.chain(),
            "steps": [step.as_dict() for step in self.steps],
        }
        slowest = self.slowest()
        if slowest:
            payload["slowest_step"] = slowest.name
            payload["slowest_ms"] = slowest.duration_ms
        if self.error_code:
            payload["error_code"] = self.error_code
        if self.error_type:
            payload["error_type"] = self.error_type
        return payload

    def attach(self, payload: dict) -> dict:
        """در صورت تنظیم YAML، trace را به پاسخ ابزار می‌چسباند.

        ورودی:
            payload: دیکشنری خروجی ابزار.
        خروجی:
            همان دیکشنری یا کپی با کلید trace.
        فراخوانی‌ها:
            load_logging_config، snapshot.
        علت:
            زمان صرف‌شده باید در خود پاسخ MCP هم قابل‌رؤیت باشد.
        """
        settings = load_logging_config()
        if not settings.get("include_trace_in_response", True):
            return payload
        attached = dict(payload)
        attached["trace"] = self.snapshot()
        return attached


def _log_line(event: str, fields: dict) -> None:
    """یک خط ساخت‌یافته روی لاگر MCP می‌نویسد."""
    logger = get_logger()
    logger.info("%s", _format_fields({"event": event, **fields}))


def _end_fields(operation: "Operation") -> dict:
    """فیلدهای مشترک پایان عملیات را می‌سازد."""
    fields = {
        "kind": operation.kind,
        "name": operation.name,
        "op": operation.op_id,
        "status": operation.status,
        "error_code": operation.error_code,
        "error_type": operation.error_type,
        "duration_ms": _ms(operation.started),
        "steps": len(operation.steps),
        "chain": operation.chain() or None,
    }
    slowest = operation.slowest()
    if slowest:
        fields["slowest"] = slowest.name
        fields["slowest_ms"] = slowest.duration_ms
    return fields


@contextmanager
def log_operation(name: str, kind: str = "tool"):
    """شروع و پایان یک عملیات MCP را با duration_ms لاگ می‌کند.

    ورودی:
        name: نام ابزار یا منبع یا پرامپت، مثلاً list_users.
        kind: نوع عملیات؛ پیش‌فرض tool.
    خروجی:
        context manager که Operation می‌دهد.
    فراخوانی‌ها:
        time.perf_counter، get_logger.
    علت:
        حتی اگر مرحله‌ای خطا بدهد، مدت کل باید ثبت شود.
    """
    operation = Operation(
        kind=kind,
        name=name,
        op_id=uuid.uuid4().hex[:8],
        started=time.perf_counter(),
    )
    token = _current_operation.set(operation)
    _log_line(
        "start",
        {"kind": kind, "name": name, "op": operation.op_id},
    )
    try:
        yield operation
    except Exception as exc:
        operation.status = "error"
        operation.error_code = getattr(exc, "error_code", None)
        operation.error_type = type(exc).__name__
        _log_line("end", _end_fields(operation))
        raise
    else:
        _log_line("end", _end_fields(operation))
    finally:
        _current_operation.reset(token)


@contextmanager
def log_step(name: str, detail: str, module: str | None = None):
    """یک مرحله داخل عملیات جاری را زمان‌گیری و لاگ می‌کند.

    ورودی:
        name: نام مرحله مثل fetch یا validate.
        detail: نام تابع، مثلاً fetch_users.
        module: ماژول تابع برای دیدن جای کد در زنجیره.
    خروجی:
        context manager بدون مقدار.
    فراخوانی‌ها:
        time.perf_counter.
    علت:
        اگر عملیات والد نباشد (مثلاً تست مستقیم سرویس) چیزی
        نوشته نمی‌شود تا خروجی تست شلوغ نشود.
    """
    operation = _current_operation.get()
    extra: dict = {}
    if operation is None:
        yield extra
        return
    seq, depth, parent, path = operation.enter_step(name)
    started = time.perf_counter()
    status = "success"
    try:
        yield extra
    except Exception as exc:
        status = "error"
        extra.setdefault("error_type", type(exc).__name__)
        extra.setdefault("error_code", getattr(exc, "error_code", None))
        raise
    finally:
        record = StepRecord(
            name=name,
            detail=detail,
            status=status,
            duration_ms=_ms(started),
            seq=seq,
            depth=depth,
            parent=parent,
            path=path,
            module=module,
            extra=dict(extra),
        )
        operation.steps.append(record)
        operation.leave_step()
        _log_line(
            "step",
            {
                "kind": operation.kind,
                "name": operation.name,
                "op": operation.op_id,
                "step": name,
                "detail": detail,
                "module": module,
                "seq": seq,
                "depth": depth,
                "parent": parent,
                "path": path,
                "status": status,
                "duration_ms": record.duration_ms,
                **record.extra,
            },
        )


def logged_step(step_name: str):
    """تابع لایه دامنه را در صورت وجود عملیات والد زمان‌گیری می‌کند.

    ورودی:
        step_name: برچسب مرحله، مثلاً fetch یا calculate.
    خروجی:
        دکوراتور که همان تابع را با حفظ نام و امضا برمی‌گرداند.
    فراخوانی‌ها:
        log_step، functools.wraps.
    علت:
        بدنهٔ سرویس عوض نشود؛ مراحل از روی توابع موجود دیده شوند.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with log_step(step_name, fn.__name__, module=fn.__module__) as extra:
                result = fn(*args, **kwargs)
                extra.update(_extra_from_result(result, step_name))
                return result

        return wrapper

    return decorator


def logged_tool(name: str, kind: str = "tool"):
    """تابع ابزار MCP را با عملیات لاگ و trace در پاسخ می‌پوشاند.

    ورودی:
        name: نام روی سیم پروتکل.
        kind: tool یا resource یا prompt.
    خروجی:
        دکوراتور با حفظ امضا برای FastMCP.
    فراخوانی‌ها:
        log_operation، Operation.attach.
    علت:
        هر ابزار بدون تکرار with در بدنه، شروع و پایان و مدت داشته باشد.
        اگر پاسخ JSON با status برابر error باشد، همان در لاگ ثبت می‌شود.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with log_operation(name, kind=kind) as operation:
                result = fn(*args, **kwargs)
                if isinstance(result, dict):
                    if result.get("status") == "error":
                        operation.status = "error"
                        operation.error_code = result.get("error_code")
                    if kind == "tool":
                        return operation.attach(result)
                return result

        return wrapper

    return decorator
