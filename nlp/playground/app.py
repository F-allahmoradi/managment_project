"""سرور HTTP محلی برای تست فکت، نقل‌قول و قاب مسئله در مرورگر.

stdio مخصوص کلاینت MCP می‌ماند. اینجا فقط localhost است.
استخراج INSERT ندارد. ذخیره پیشنهادی قاب، علت‌های تأییدشده
و وظیفه و امتیاز را با تأیید انسان به CRUD می‌فرستد.
بعد از امتیاز، موضوع و موجودیت ذخیره‌شدهٔ NER پیشنهادی است.
فکت‌های تأییدشده و نقل‌قول‌های تأییدشده روی همان تحلیل با save_text_analysis می‌مانند.
"""

from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import sys
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path, load_crud_symbol

ensure_import_path()

from business_logic.extractor import extract_facts, extract_frame, extract_quotes
from business_logic.normalizer import normalize_text
from business_logic.suggest import suggest_task_title
from errors.crud import format_crud_error, format_error
from logging_module import log_operation, setup_logging
from playground.config import bind_playground_actor, load_playground_config
from schemas.output import ExtractFactsOutput, ExtractFrameOutput, ExtractQuotesOutput
from tests.sample import SAMPLE_TEXT

_SAVE_ISSUE_INPUT = None
_SAVE_ANALYSIS_INPUT = None
_LINK_CAUSE_INPUT = None
_SAVE_TASK_INPUT = None
_LINK_TASK_INPUT = None
_SET_IMPORTANCE_INPUT = None
_SET_URGENCY_INPUT = None
_SET_SEVERITY_INPUT = None
_ADD_IMPACT_INPUT = None
_LINK_TOPIC_INPUT = None
_LINK_ENTITY_INPUT = None
_SAVE_FACT_INPUT = None
_SAVE_QUOTE_INPUT = None


def _save_issue_input_cls():
    """اسکیمای ثبت مسئله را یک‌بار، جدا از schemas همنام nlp، می‌آورد."""
    global _SAVE_ISSUE_INPUT
    if _SAVE_ISSUE_INPUT is None:
        _SAVE_ISSUE_INPUT = load_crud_symbol("schemas.crud.issue", "CreateIssueInput")
    return _SAVE_ISSUE_INPUT


def _link_cause_input_cls():
    """اسکیمای وصل علت را یک‌بار، جدا از schemas همنام nlp، می‌آورد."""
    global _LINK_CAUSE_INPUT
    if _LINK_CAUSE_INPUT is None:
        _LINK_CAUSE_INPUT = load_crud_symbol("schemas.crud.issue", "LinkIssueCauseInput")
    return _LINK_CAUSE_INPUT


def _save_task_input_cls():
    """اسکیمای ثبت وظیفه را یک‌بار، جدا از schemas همنام nlp، می‌آورد."""
    global _SAVE_TASK_INPUT
    if _SAVE_TASK_INPUT is None:
        _SAVE_TASK_INPUT = load_crud_symbol("schemas.crud.task", "CreateTaskInput")
    return _SAVE_TASK_INPUT


def _link_task_input_cls():
    """اسکیمای وصل وظیفه به مسئله را یک‌بار از کراد می‌آورد."""
    global _LINK_TASK_INPUT
    if _LINK_TASK_INPUT is None:
        _LINK_TASK_INPUT = load_crud_symbol("schemas.crud.issue", "LinkIssueTaskInput")
    return _LINK_TASK_INPUT


def _set_importance_input_cls():
    """اسکیمای تنظیم اهمیت مسئله را یک‌بار از کراد می‌آورد."""
    global _SET_IMPORTANCE_INPUT
    if _SET_IMPORTANCE_INPUT is None:
        _SET_IMPORTANCE_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "SetIssueImportanceInput",
        )
    return _SET_IMPORTANCE_INPUT


def _set_urgency_input_cls():
    """اسکیمای تنظیم فوریت مسئله را یک‌بار از کراد می‌آورد."""
    global _SET_URGENCY_INPUT
    if _SET_URGENCY_INPUT is None:
        _SET_URGENCY_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "SetIssueUrgencyInput",
        )
    return _SET_URGENCY_INPUT


def _set_severity_input_cls():
    """اسکیمای تنظیم شدت مسئله را یک‌بار از کراد می‌آورد."""
    global _SET_SEVERITY_INPUT
    if _SET_SEVERITY_INPUT is None:
        _SET_SEVERITY_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "SetIssueSeverityInput",
        )
    return _SET_SEVERITY_INPUT


def _add_impact_input_cls():
    """اسکیمای افزودن اثر مسئله را یک‌بار از کراد می‌آورد."""
    global _ADD_IMPACT_INPUT
    if _ADD_IMPACT_INPUT is None:
        _ADD_IMPACT_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "AddIssueImpactInput",
        )
    return _ADD_IMPACT_INPUT


def _link_topic_input_cls():
    """اسکیمای وصل موضوع به مسئله را یک‌بار از کراد می‌آورد."""
    global _LINK_TOPIC_INPUT
    if _LINK_TOPIC_INPUT is None:
        _LINK_TOPIC_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "LinkIssueTopicInput",
        )
    return _LINK_TOPIC_INPUT


def _link_entity_input_cls():
    """اسکیمای وصل موجودیت به مسئله را یک‌بار از کراد می‌آورد."""
    global _LINK_ENTITY_INPUT
    if _LINK_ENTITY_INPUT is None:
        _LINK_ENTITY_INPUT = load_crud_symbol(
            "schemas.crud.issue",
            "LinkIssueEntityInput",
        )
    return _LINK_ENTITY_INPUT


def _save_analysis_input_cls():
    """اسکیمای ذخیره تحلیل را یک‌بار، جدا از schemas همنام nlp، می‌آورد."""
    global _SAVE_ANALYSIS_INPUT
    if _SAVE_ANALYSIS_INPUT is None:
        _SAVE_ANALYSIS_INPUT = load_crud_symbol(
            "schemas.crud.text_analysis",
            "SaveTextAnalysisInput",
        )
    return _SAVE_ANALYSIS_INPUT


def _save_fact_input_cls():
    """اسکیمای یک فکت ذخیره‌شونده را یک‌بار از کراد می‌آورد."""
    global _SAVE_FACT_INPUT
    if _SAVE_FACT_INPUT is None:
        _SAVE_FACT_INPUT = load_crud_symbol(
            "schemas.crud.text_analysis",
            "SaveFactInput",
        )
    return _SAVE_FACT_INPUT


def _save_quote_input_cls():
    """اسکیمای یک نقل‌قول ذخیره‌شونده را یک‌بار از کراد می‌آورد."""
    global _SAVE_QUOTE_INPUT
    if _SAVE_QUOTE_INPUT is None:
        _SAVE_QUOTE_INPUT = load_crud_symbol(
            "schemas.crud.text_analysis",
            "SaveQuoteInput",
        )
    return _SAVE_QUOTE_INPUT

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
    "facts": extract_facts,
    "quotes": extract_quotes,
    "frame": extract_frame,
}
_LAYER_LABELS = {
    "facts": "فکت",
    "quotes": "نقل‌قول",
    "frame": "قاب مسئله",
}
_TOOL_BY_LAYER = {
    "facts": "extract_facts",
    "quotes": "extract_quotes",
    "frame": "extract_frame",
}


def _run_traced(name: str, text: str) -> dict:
    """یک لایه را با عملیات لاگ اجرا می‌کند تا نام ابزار و مدت در پاسخ بیاید."""
    tool = _TOOL_BY_LAYER[name]
    with log_operation(tool) as operation:
        try:
            result = _LAYERS[name](text)
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
        return operation.attach(_attach_suggested_task(payload))


def _dump_layer(name: str, text: str) -> dict:
    """یک لایه را اجرا و به JSON تبدیل می‌کند."""
    return _run_traced(name, text)


def _empty_layer(name: str, text: str):
    """خروجی خالی یک لایه را می‌سازد تا بقیهٔ لایه‌ها دور ریخته نشوند."""
    length = len(normalize_text(text))
    if name == "quotes":
        return ExtractQuotesOutput(
            status="success",
            message="نقل‌قولی استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    if name == "frame":
        return ExtractFrameOutput(
            status="success",
            message="قاب مسئله استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    return ExtractFactsOutput(
        status="success",
        message="فکتی استخراج نشد",
        source="project_texts",
        text_length=length,
        explicitness="none",
        explicitness_name="بدون فکت",
    )


def _collect_layers(text: str) -> tuple[dict, dict]:
    """هر لایه را جدا اجرا می‌کند تا timeout یکی بقیه را نبرد."""
    parts = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(fn, text) for name, fn in _LAYERS.items()}
        for name, future in futures.items():
            try:
                parts[name] = future.result()
            except Exception as exc:
                errors[name] = exc
                parts[name] = _empty_layer(name, text)
    return parts, errors


def _dump_all(text: str) -> dict:
    """سه لایه را اجرا می‌کند؛ شکست یکی بقیه را دور نمی‌ریزد."""
    parts, errors = _collect_layers(text)
    if len(errors) == len(_LAYERS):
        raise next(iter(errors.values()))
    facts = parts["facts"]
    quotes = parts["quotes"]
    frame = parts["frame"]
    payload = facts.model_dump()
    payload["quotes"] = [item.model_dump() for item in quotes.quotes]
    payload["quote_count"] = quotes.quote_count
    payload["frame"] = frame.frame.model_dump() if frame.frame is not None else None
    payload["normalized_text"] = normalize_text(text)
    payload["layer"] = "all"
    bits = [facts.message]
    if quotes.quotes:
        bits.append(quotes.message)
    if frame.frame is not None:
        bits.append(frame.message)
    for name, exc in errors.items():
        packed = format_error(exc)
        bits.append(
            f"{_LAYER_LABELS[name]} نیامد: {packed.get('message') or 'خطای مدل'}"
        )
    payload["message"] = "؛ ".join(bits)
    payload["layer_errors"] = {
        name: format_error(exc).get("message") for name, exc in errors.items()
    }
    return _attach_suggested_task(payload)


def _positive_int(value):
    """عدد صحیح مثبت را برمی‌گرداند یا None."""
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 1:
        return None
    return number


def _resolve_project_id(body: dict, actor_id: int) -> int:
    """پروژه را از بدنه، YAML، یا اولین عضویت فعال بازیگر برمی‌دارد."""
    from errors.crud import InvalidInputError
    from services.project import fetch_projects_for_actor

    project_id = _positive_int(body.get("project_id"))
    if project_id is not None:
        return project_id
    settings = load_playground_config()
    configured = _positive_int(settings.get("project_id"))
    if configured is not None:
        return configured
    rows = fetch_projects_for_actor(actor_id, limit=1, offset=0)
    if not rows:
        raise InvalidInputError("پروژه‌ای برای ذخیره مسئله پیدا نشد")
    return rows[0]["id"]


def _attach_suggested_task(payload: dict) -> dict:
    """عنوان پیشنهادی وظیفه را از نیت یا قاب روی همان پاسخ می‌گذارد."""
    suggested = suggest_task_title(
        intents=payload.get("intents"),
        frame=payload.get("frame"),
        facts=payload.get("facts"),
    )
    if suggested:
        payload["suggested_task"] = suggested
        payload["suggested_scoring"] = _catalog_scoring(_DEFAULT_TASK_PRIORITY)
    return payload


def _ensure_analysis_id(body: dict, actor_id: int) -> tuple[int, dict]:
    """اگر تحلیل از قبل باشد همان را می‌دهد؛ وگرنه save_text_analysis می‌زند.

    فکت‌ها و نقل‌قول‌های تأییدشده در هر دو حالت روی همان تحلیل نوشته می‌شوند.
    """
    from auth.gate import require_permission
    from errors.crud import InvalidInputError
    from services.text_analysis import (
        insert_text_analysis,
        insert_text_analysis_facts,
        insert_text_analysis_quotes,
    )

    facts = _confirmed_facts(body)
    quotes = _confirmed_quotes(body)
    analysis_id = _positive_int(body.get("analysis_id"))
    if analysis_id is not None:
        stored_facts = []
        stored_quotes = []
        if facts or quotes:
            require_permission("TextAnalysis", "Create")
            if facts:
                stored_facts = insert_text_analysis_facts(
                    analysis_id,
                    facts,
                    created_by=actor_id,
                )
            if quotes:
                stored_quotes = insert_text_analysis_quotes(
                    analysis_id,
                    quotes,
                    created_by=actor_id,
                )
        return analysis_id, {
            "id": analysis_id,
            "reused": True,
            "facts": stored_facts,
            "quotes": stored_quotes,
        }
    require_permission("TextAnalysis", "Create")
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise InvalidInputError("متن خالی است")
    fields = {
        "source_type": body.get("source_type") or "content",
        "source_id": body.get("source_id"),
        "text": text.strip(),
        "facts": facts,
        "quotes": quotes,
    }
    if isinstance(body.get("model"), str) and body.get("model").strip():
        fields["model"] = body["model"].strip()
    parsed = _save_analysis_input_cls()(**fields).model_dump()
    stored = insert_text_analysis(parsed, created_by=actor_id)
    return stored["id"], stored


def _confirmed_facts(body: dict) -> list:
    """فکت‌های تأییدشده را از بدنه برمی‌دارد؛ بدون فهرست یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("facts")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise InvalidInputError("فکت‌ها باید فهرست باشند")
    cls = _save_fact_input_cls()
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidInputError("هر فکت باید شیء باشد")
        parsed = cls(**item).model_dump()
        key = parsed.get("fact_id") or (
            parsed.get("kind"),
            parsed.get("name"),
            parsed.get("value"),
            parsed.get("role"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(parsed)
    return out


def _confirmed_quotes(body: dict) -> list:
    """نقل‌قول‌های تأییدشده را از بدنه برمی‌دارد؛ بدون فهرست یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("quotes")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise InvalidInputError("نقل‌قول‌ها باید فهرست باشند")
    cls = _save_quote_input_cls()
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidInputError("هر نقل‌قول باید شیء باشد")
        parsed = cls(**item).model_dump()
        key = (
            parsed.get("mode"),
            parsed.get("attributed_to"),
            parsed.get("quoted_text"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(parsed)
    return out


def _confirmed_causes(body: dict) -> list:
    """فکت‌های علت تأییدشده را از بدنه برمی‌دارد؛ بدون فهرست یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("causes")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise InvalidInputError("علت‌ها باید فهرست باشند")
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidInputError("هر علت باید شیء باشد")
        cause_issue_id = _positive_int(item.get("cause_issue_id"))
        title = str(item.get("title") or item.get("name") or "").strip()
        if cause_issue_id is None and not title:
            raise InvalidInputError("عنوان یا شناسه علت لازم است")
        key = ("id", cause_issue_id) if cause_issue_id is not None else ("title", title)
        if key in seen:
            continue
        seen.add(key)
        cause = {}
        if cause_issue_id is not None:
            cause["cause_issue_id"] = cause_issue_id
        if title:
            cause["title"] = title[:200]
        level = item.get("cause_level") or item.get("level")
        if isinstance(level, str) and level.strip():
            cause["cause_level"] = level.strip()
        level_id = _positive_int(item.get("cause_level_id"))
        if level_id is not None:
            cause["cause_level_id"] = level_id
        out.append(cause)
    return out


def _ensure_cause_issue(
    item: dict,
    project_id: int,
    analysis_id: int,
    created_by: int,
    effect_title: str,
):
    """مسئلهٔ علت را می‌سازد یا مسئلهٔ موجود همین پروژه را برمی‌دارد."""
    from services.issue import find_issue_in_project, insert_issue

    cause_issue_id = item.get("cause_issue_id")
    if cause_issue_id is not None:
        return cause_issue_id, True
    title = item.get("title") or ""
    if not title or title == effect_title:
        return None, False
    existing = find_issue_in_project(project_id, title)
    if existing is not None:
        return existing["id"], True
    fields = {
        "project_id": project_id,
        "title": title,
        "analysis_id": analysis_id,
    }
    parsed = _save_issue_input_cls()(**fields).model_dump()
    stored = insert_issue(parsed, created_by=created_by)
    return stored["id"], False


def _attach_causes(
    main: dict,
    causes: list,
    project_id: int,
    analysis_id: int,
    created_by: int,
) -> list:
    """هر علت تأییدشده را مسئله می‌کند و با link_issue_cause وصل می‌کند."""
    from services.issue import insert_issue_cause

    linked = []
    for item in causes:
        cause_issue_id, reused = _ensure_cause_issue(
            item,
            project_id,
            analysis_id,
            created_by,
            main["title"],
        )
        if cause_issue_id is None or cause_issue_id == main["id"]:
            continue
        fields = {
            "issue_id": main["id"],
            "cause_issue_id": cause_issue_id,
        }
        if item.get("cause_level"):
            fields["cause_level"] = item["cause_level"]
        if item.get("cause_level_id") is not None:
            fields["cause_level_id"] = item["cause_level_id"]
        parsed = _link_cause_input_cls()(**fields).model_dump()
        row = insert_issue_cause(parsed, created_by=created_by)
        packed = dict(row)
        packed["reused"] = reused
        linked.append(packed)
    return linked


_DEFAULT_TASK_STATUS = "شروع نشده"
_DEFAULT_TASK_PRIORITY = "کم"
_DEFAULT_TASK_IMPORTANCE = "کم"
_SUGGESTED_ISSUE_IMPORTANCE = "زیاد"
_SUGGESTED_ISSUE_SEVERITY = "متوسط"
_SUGGESTED_ISSUE_IMPACTS = ("منابع انسانی", "کیفیت")


def _catalog_scoring(urgency: str) -> dict:
    """پیشنهاد امتیاز از کاتالوگ seed؛ استخراج LLM نیست."""
    return {
        "importance": _SUGGESTED_ISSUE_IMPORTANCE,
        "urgency": urgency,
        "severity": _SUGGESTED_ISSUE_SEVERITY,
        "impacts": [
            {"impact_type": name, "description": name}
            for name in _SUGGESTED_ISSUE_IMPACTS
        ],
    }


def _confirmed_task(body: dict, frame: dict):
    """وظیفهٔ تأییدشده را از بدنه برمی‌دارد؛ بدون کلید یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("task")
    if raw is None:
        return None
    if raw is False:
        return None
    if not isinstance(raw, dict):
        raise InvalidInputError("وظیفه باید شیء باشد")
    task_id = _positive_int(raw.get("id") or raw.get("task_id"))
    if task_id is not None:
        return {"task_id": task_id}
    title = str(raw.get("title") or "").strip()
    if not title:
        suggested = suggest_task_title(
            intents=body.get("intents") or raw.get("intents"),
            frame=frame,
            facts=body.get("facts"),
        )
        title = (suggested or {}).get("title") or ""
    if not title:
        raise InvalidInputError("عنوان وظیفه خالی است")
    return {"title": title[:200]}


def _attach_task(
    main: dict,
    confirmed: dict,
    project_id: int,
    created_by: int,
) -> dict:
    """وظیفه را با create_task می‌سازد یا موجود را با link_issue_task وصل می‌کند."""
    from auth.gate import require_permission
    from services.issue import insert_issue_task
    from services.task import insert_task

    task_id = confirmed.get("task_id")
    created = False
    if task_id is None:
        require_permission("Task", "Create")
        fields = {
            "project_id": project_id,
            "title": confirmed["title"],
            "status": _DEFAULT_TASK_STATUS,
            "priority": _DEFAULT_TASK_PRIORITY,
            "importance": _DEFAULT_TASK_IMPORTANCE,
        }
        parsed = _save_task_input_cls()(**fields).model_dump()
        task_id = insert_task(parsed, created_by=created_by)
        created = True
    link_fields = {"issue_id": main["id"], "task_id": task_id}
    parsed_link = _link_task_input_cls()(**link_fields).model_dump()
    row = insert_issue_task(parsed_link, created_by=created_by)
    packed = dict(row)
    packed["created"] = created
    packed["task_id"] = task_id
    packed["issue_id"] = main["id"]
    packed["title"] = packed.get("task_title") or confirmed.get("title") or ""
    return packed


_AFFECTED_ENTITY_TYPES = frozenset({"UNIT", "ORG"})
_DEFAULT_ENTITY_ROLE = "mentioned"
_DEFAULT_ENTITY_ROLE_NAME = "ذکرشده"


def _suggested_entity_role(entity_type: str) -> tuple[str, str]:
    """نقش پیشنهادی موجودیت: واحد/سازمان متأثر، بقیه ذکرشده."""
    if entity_type in _AFFECTED_ENTITY_TYPES:
        return "affected", "متأثر"
    return _DEFAULT_ENTITY_ROLE, _DEFAULT_ENTITY_ROLE_NAME


def _suggest_issue_ner(analysis_id: int) -> dict:
    """موضوع و موجودیت ذخیره‌شدهٔ همان تحلیل را بدون استخراج جدید می‌خواند."""
    from repository import (
        fetch_text_analysis_entities_records,
        fetch_text_analysis_topics_records,
    )

    topics = []
    for row in fetch_text_analysis_topics_records(analysis_id):
        topics.append(
            {
                "topic_id": row.get("topic_id"),
                "code": row.get("code"),
                "name": row.get("name"),
                "is_primary": row.get("is_primary"),
                "mention_text": row.get("mention_text"),
            }
        )
    entities = []
    for row in fetch_text_analysis_entities_records(analysis_id):
        entity_type = row.get("type") or ""
        role, role_name = _suggested_entity_role(entity_type)
        entities.append(
            {
                "entity_id": row.get("id"),
                "canonical_name": row.get("canonical_name"),
                "type": entity_type,
                "role": role,
                "role_name": role_name,
            }
        )
    return {"topics": topics, "entities": entities}


def _confirmed_topics(body: dict):
    """موضوع‌های تأییدشده را از بدنه برمی‌دارد؛ بدون کلید یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("topics")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise InvalidInputError("موضوع‌ها باید فهرست باشند")
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidInputError("هر موضوع باید شیء باشد")
        topic_id = _positive_int(item.get("topic_id") or item.get("id"))
        code = str(item.get("code") or item.get("topic") or "").strip()
        if topic_id is None and not code:
            raise InvalidInputError("شناسه یا کد موضوع لازم است")
        key = ("id", topic_id) if topic_id is not None else ("code", code)
        if key in seen:
            continue
        seen.add(key)
        packed = {}
        if topic_id is not None:
            packed["topic_id"] = topic_id
        if code:
            packed["topic"] = code
        out.append(packed)
    return out


def _confirmed_entities(body: dict):
    """موجودیت‌های تأییدشده را از بدنه برمی‌دارد؛ بدون کلید یعنی هیچ."""
    from errors.crud import InvalidInputError

    raw = body.get("entities")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise InvalidInputError("موجودیت‌ها باید فهرست باشند")
    out = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidInputError("هر موجودیت باید شیء باشد")
        entity_id = _positive_int(item.get("entity_id") or item.get("id"))
        if entity_id is None:
            raise InvalidInputError("شناسه موجودیت لازم است")
        role = str(item.get("role") or "").strip()
        role_id = _positive_int(item.get("role_id"))
        key = (entity_id, role or role_id)
        if key in seen:
            continue
        seen.add(key)
        packed = {"entity_id": entity_id}
        if role:
            packed["role"] = role
        if role_id is not None:
            packed["role_id"] = role_id
        out.append(packed)
    return out


def _attach_issue_ner(
    issue: dict,
    topics: list,
    entities: list,
    created_by: int,
) -> tuple[list, list]:
    """موضوع و موجودیت تأییدشده را به مسئله وصل می‌کند؛ تکراری را رد می‌کند."""
    from services.issue import insert_issue_entity, insert_issue_topic

    existing_topics = {row.get("topic_id") for row in issue.get("topics") or []}
    existing_entities = {
        (row.get("entity_id"), row.get("role_code"))
        for row in issue.get("entities") or []
    }
    linked_topics = []
    for item in topics:
        topic_id = item.get("topic_id")
        if topic_id is not None and topic_id in existing_topics:
            continue
        fields = {"issue_id": issue["id"]}
        if topic_id is not None:
            fields["topic_id"] = topic_id
        if item.get("topic"):
            fields["topic"] = item["topic"]
        parsed = _link_topic_input_cls()(**fields).model_dump()
        row = insert_issue_topic(parsed, created_by=created_by)
        existing_topics.add(row.get("topic_id"))
        linked_topics.append(row)
    linked_entities = []
    for item in entities:
        entity_id = item["entity_id"]
        role = item.get("role") or _DEFAULT_ENTITY_ROLE
        if (entity_id, role) in existing_entities:
            continue
        fields = {"issue_id": issue["id"], "entity_id": entity_id, "role": role}
        if item.get("role_id") is not None:
            fields["role_id"] = item["role_id"]
        parsed = _link_entity_input_cls()(**fields).model_dump()
        row = insert_issue_entity(parsed, created_by=created_by)
        existing_entities.add((row.get("entity_id"), row.get("role_code")))
        linked_entities.append(row)
    return linked_topics, linked_entities


def _scoring_from_issue(stored: dict):
    """امتیاز ثبت‌شدهٔ مسئله را برای پاسخ playground برمی‌گرداند."""
    importance = stored.get("importance") or {}
    if not importance:
        return None
    urgency = stored.get("urgency") or {}
    severity = stored.get("severity") or {}
    impacts = stored.get("impacts") or []
    return {
        "importance": importance.get("importance_name"),
        "urgency": urgency.get("priority_name"),
        "severity": severity.get("severity_name"),
        "impacts": [item.get("impact_type_name") for item in impacts],
        "status": "saved",
    }


def _task_from_issue(stored: dict):
    """اولین وظیفهٔ وصل‌شده را برای پاسخ playground برمی‌گرداند."""
    rows = stored.get("tasks") or []
    if not rows:
        return None
    row = dict(rows[0])
    row["created"] = False
    row["title"] = row.get("task_title") or ""
    return row


def _attach_scoring(main: dict, urgency: str, created_by: int) -> dict:
    """اهمیت، فوریت، شدت و اثر پیشنهادی کاتالوگ را بعد از وظیفه می‌نویسد."""
    from services.issue import (
        add_issue_impact,
        set_issue_importance,
        set_issue_severity,
        set_issue_urgency,
    )

    issue_id = main["id"]
    importance = set_issue_importance(
        _set_importance_input_cls()(
            issue_id=issue_id,
            importance=_SUGGESTED_ISSUE_IMPORTANCE,
        ).model_dump(),
        created_by=created_by,
    )
    urgency_row = set_issue_urgency(
        _set_urgency_input_cls()(
            issue_id=issue_id,
            priority=urgency,
        ).model_dump(),
        created_by=created_by,
    )
    severity = set_issue_severity(
        _set_severity_input_cls()(
            issue_id=issue_id,
            severity=_SUGGESTED_ISSUE_SEVERITY,
        ).model_dump(),
        created_by=created_by,
    )
    impacts = []
    for name in _SUGGESTED_ISSUE_IMPACTS:
        row = add_issue_impact(
            _add_impact_input_cls()(
                issue_id=issue_id,
                impact_type=name,
                description=name,
            ).model_dump(),
            created_by=created_by,
        )
        impacts.append(row)
    return {
        "importance": importance.get("importance_name"),
        "urgency": urgency_row.get("priority_name"),
        "severity": severity.get("severity_name"),
        "impacts": [item.get("impact_type_name") for item in impacts],
        "importance_row": importance,
        "urgency_row": urgency_row,
        "severity_row": severity,
        "impact_rows": impacts,
        "status": "saved",
    }


def _save_issue(body: dict) -> dict:
    """قاب و علت و وظیفه و امتیاز و سپس موضوع/موجودیت NER را می‌نویسد."""
    from auth.gate import require_permission
    from errors.crud import InvalidInputError, format_success
    from services.issue import insert_issue

    frame = body.get("frame")
    if not isinstance(frame, dict):
        raise InvalidInputError("قاب مسئله استخراج نشده")
    title = str(frame.get("title") or "").strip()
    if not title:
        raise InvalidInputError("عنوان مسئله خالی است")
    actor = require_permission("Issue", "Create")
    analysis_id, analysis = _ensure_analysis_id(body, actor["id"])
    project_id = _resolve_project_id(body, actor["id"])
    fields = {
        "project_id": project_id,
        "title": title[:200],
        "analysis_id": analysis_id,
    }
    status = body.get("status")
    if isinstance(status, str) and status.strip():
        fields["status"] = status.strip()
    status_id = _positive_int(body.get("status_id"))
    if status_id is not None:
        fields["status_id"] = status_id
    parsed = _save_issue_input_cls()(**fields).model_dump()
    stored = insert_issue(parsed, created_by=actor["id"])
    packed = format_success("مسئله با وضعیت پیشنهادی ثبت شد", **stored)
    packed["analysis_id"] = analysis_id
    packed["reused"] = bool(stored.get("reused"))
    packed["facts"] = analysis.get("facts") or []
    packed["fact_count"] = len(packed["facts"])
    packed["quotes"] = analysis.get("quotes") or []
    packed["quote_count"] = len(packed["quotes"])
    if analysis.get("reused"):
        packed["analysis_reused"] = True
    elif analysis.get("source_id") is not None:
        packed["analysis"] = {
            "id": analysis_id,
            "source_type": analysis.get("source_type"),
            "source_id": analysis.get("source_id"),
        }
    bits = [packed["message"]]
    if packed["facts"]:
        bits.append(f"{len(packed['facts'])} فکت روی تحلیل ماند")
    if packed["quotes"]:
        bits.append(f"{len(packed['quotes'])} نقل‌قول روی تحلیل ماند")
    if stored.get("reused"):
        packed["causes"] = stored.get("causes") or []
    else:
        causes = _attach_causes(
            stored,
            _confirmed_causes(body),
            project_id,
            analysis_id,
            actor["id"],
        )
        packed["causes"] = causes
        if causes:
            bits.append(f"{len(causes)} علت وصل شد")
    confirmed = _confirmed_task(body, frame)
    if confirmed is not None:
        existing_task = _task_from_issue(stored)
        if existing_task is not None:
            packed["task"] = existing_task
        else:
            from services.task import fetch_task

            task = _attach_task(stored, confirmed, project_id, actor["id"])
            packed["task"] = task
            bits.append("وظیفه وصل شد")
            task_row = fetch_task(task["task_id"])
            urgency = task_row.get("priority_name") or _DEFAULT_TASK_PRIORITY
            scoring = _attach_scoring(stored, urgency, actor["id"])
            packed["scoring"] = scoring
            bits.append("امتیاز مسئله ثبت شد")
    if packed.get("scoring") is None:
        packed_scoring = _scoring_from_issue(stored)
        if packed_scoring is not None:
            packed["scoring"] = packed_scoring
    if packed.get("scoring"):
        suggestions = _suggest_issue_ner(analysis_id)
        packed["suggested_topics"] = suggestions["topics"]
        packed["suggested_entities"] = suggestions["entities"]
        confirmed_topics = _confirmed_topics(body)
        confirmed_entities = _confirmed_entities(body)
        if confirmed_topics is not None or confirmed_entities is not None:
            topics, entities = _attach_issue_ner(
                stored,
                confirmed_topics or [],
                confirmed_entities or [],
                actor["id"],
            )
            packed["topics"] = topics or stored.get("topics") or []
            packed["entities"] = entities or stored.get("entities") or []
            if topics or entities:
                bits.append("موضوع و موجودیت به مسئله وصل شد")
        else:
            packed["topics"] = stored.get("topics") or []
            packed["entities"] = stored.get("entities") or []
    packed["message"] = "؛ ".join(bits)
    return packed


class PlaygroundHandler(BaseHTTPRequestHandler):
    """صفحهٔ استاتیک و API استخراج فکت را پاسخ می‌دهد."""

    server_version = "management-nlp-playground/1"

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
        if path == "/api/sample":
            self._send(
                200,
                {
                    "text": SAMPLE_TEXT,
                    "note": "متن ساختگی است؛ از دیتابیس نیامده. درصد، علت و نقل‌قول دارد.",
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
        if path == "/api/save":
            try:
                self._send(200, _save_issue(body))
            except Exception as exc:
                self._send(200, format_crud_error(exc))
            return
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
        if path == "/api/extract":
            try:
                self._send(200, _dump_all(text.strip()))
            except Exception as exc:
                self._send(200, format_error(exc))
            return
        if path.startswith("/api/extract/"):
            layer = path[len("/api/extract/") :]
            if layer not in _LAYERS:
                self._send(404, {"error": "مسیر پیدا نشد"})
                return
            try:
                self._send(200, _dump_layer(layer, text.strip()))
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
    _save_issue_input_cls()
    _save_analysis_input_cls()
    _save_fact_input_cls()
    _link_cause_input_cls()
    _save_task_input_cls()
    _link_task_input_cls()
    _set_importance_input_cls()
    _set_urgency_input_cls()
    _set_severity_input_cls()
    _add_impact_input_cls()
    _link_topic_input_cls()
    _link_entity_input_cls()
    actor_label = bind_playground_actor()
    httpd = ThreadingHTTPServer((bind_host, bind_port), PlaygroundHandler)
    url = f"http://{bind_host}:{bind_port}"
    actor_bit = f" · بازیگر {actor_label}" if actor_label else ""
    sys.stderr.write(f"زمین بازی فکت و قاب: {url}{actor_bit}\nقطع با Ctrl+C\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\nزمین بازی بسته شد.\n")
    finally:
        httpd.server_close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="زمین بازی فکت، نقل‌قول و قاب مسئله")
    parser.add_argument("--host", default=None, help="میزبان؛ پیش‌فرض از playground.yaml")
    parser.add_argument("--port", type=int, default=None, help="پورت؛ پیش‌فرض ۸۷۸۰")
    args = parser.parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
