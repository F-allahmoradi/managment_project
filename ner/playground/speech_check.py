"""سنجش ژانر و نیت برای زمین‌بازی تست دستی.

مدل را صدا نمی‌زند؛ خروجی استخراج را با انتظار کاربر مقایسه می‌کند.
"""

from business_logic.config import (
    load_column_config,
    load_discourse_catalog,
    load_entity_config,
    load_intent_catalog,
    load_rhetoric_catalog,
    load_stance_catalog,
    load_topic_catalog,
)
from tests.sample import SAMPLE_TEXT

JOINT_EXAMPLES = [
    {
        "label": "مسئله",
        "text": "سرور پشتیبان از دیشب قطع است.",
        "expected_discourse": "issue",
        "expected_intent": "report_problem",
        "expected_rhetoric": "literal",
        "note": "مسئله بدون مقصر",
    },
    {
        "label": "درخواست",
        "text": "لطفاً امشب سرور را بالا بیاورید.",
        "expected_discourse": "request",
        "expected_intent": "request_action",
        "expected_rhetoric": "literal",
        "note": "درخواست اقدام",
    },
    {
        "label": "شکایت",
        "text": "پیمانکار بی‌هماهنگی برق را قطع کرد؛ خسارت را در صورت‌جلسه می‌خواهم.",
        "expected_discourse": "issue",
        "expected_intent": "complaint",
        "expected_rhetoric": "literal",
        "note": "مسئله با نیت شکایت",
    },
    {
        "label": "سؤال",
        "text": "علت تأخیر پرداخت چیست؟",
        "expected_discourse": "question",
        "expected_intent": "request_info",
        "expected_rhetoric": "literal",
        "note": "سؤال برای دانستن",
    },
    {
        "label": "تصمیم",
        "text": "قرار شد اسپرینت بعد فقط داشبورد باشد.",
        "expected_discourse": "decision",
        "expected_intent": "inform",
        "expected_rhetoric": "literal",
        "note": "تصمیم اعلام‌شده",
    },
    {
        "label": "پیگیری",
        "text": "همان قطعی دوشنبه هنوز درست نشده.",
        "expected_discourse": "issue",
        "expected_intent": "follow_up",
        "expected_rhetoric": "literal",
        "note": "پیگیری مورد باز",
    },
    {
        "label": "هشدار",
        "text": "ممکن است دوشنبه دیسک سرور پر شود.",
        "expected_discourse": "warning",
        "expected_intent": "inform",
        "expected_rhetoric": "literal",
        "note": "هشدار آینده",
    },
    {
        "label": "درخواست تصمیم",
        "text": "تا ساعت ۶ بگویید سوئیچ کنیم یا نه.",
        "expected_discourse": "request",
        "expected_intent": "request_decision",
        "expected_rhetoric": "literal",
        "note": "درخواست تصمیم نه اجرا",
    },
    {
        "label": "کنایه",
        "text": "چه عالی، باز هم سرور قطع شد.",
        "expected_discourse": "issue",
        "expected_intent": "objection",
        "expected_rhetoric": "irony",
        "note": "اعتراض کنایه‌ای",
    },
    {
        "label": "طعنه",
        "text": "دست واحد مالی درد نکنه، فقط سه هفته تأخیر.",
        "expected_discourse": "feedback",
        "expected_intent": "objection",
        "expected_rhetoric": "sarcasm",
        "note": "طعنه به واحد",
    },
    {
        "label": "سؤال بلاغی",
        "text": "تا کی باید دنبال صورت‌وضعیت بدویم؟",
        "expected_discourse": "issue",
        "expected_intent": "follow_up",
        "expected_rhetoric": "rhetorical_question",
        "note": "سؤال بلاغی برای پیگیری",
    },
    {
        "label": "استعاره",
        "text": "این قرارداد شده چاه.",
        "expected_discourse": "issue",
        "expected_intent": "report_problem",
        "expected_rhetoric": "metaphor",
        "note": "استعاره برای مسئله",
    },
    {
        "label": "تعریف واقعی",
        "text": "چه عالی که سرور بالا آمد.",
        "expected_discourse": "result",
        "expected_intent": "inform",
        "expected_rhetoric": "literal",
        "note": "تعریف واقعی نه کنایه",
    },
]


def _option(item: dict) -> dict:
    """کد و نام را برای فهرست انتخاب برمی‌گرداند."""
    return {
        "code": str(item["code"]),
        "name": str(item["name"]),
        "definition": str(item.get("definition") or ""),
        "accept_example": str(item.get("accept_example") or ""),
        "discovered": bool(item.get("discovered")),
    }


def _sample_row(
    *,
    label: str,
    text: str,
    group: str,
    note: str = "",
    expected_discourse: str = "",
    expected_intent: str = "",
    expected_rhetoric: str = "",
) -> dict:
    """یک دکمهٔ نمونه برای زمین‌بازی می‌سازد."""
    return {
        "label": label,
        "text": text,
        "group": group,
        "note": note,
        "expected_discourse": expected_discourse,
        "expected_intent": expected_intent,
        "expected_rhetoric": expected_rhetoric,
    }


def _accept_examples(catalog: list[dict], layer: str) -> list[dict]:
    """مثال قبول هر برچسب را به مورد تست تبدیل می‌کند."""
    examples = []
    for item in catalog:
        text = str(item.get("accept_example") or "").strip()
        if not text:
            continue
        row = _sample_row(
            label=str(item["name"]),
            text=text,
            group=layer,
            note=f"قبول {item['name']}",
        )
        if layer == "discourse":
            row["expected_discourse"] = str(item["code"])
        elif layer == "rhetoric":
            row["expected_rhetoric"] = str(item["code"])
        else:
            row["expected_intent"] = str(item["code"])
        examples.append(row)
    return examples


def _entity_types() -> list[dict]:
    """نوع‌های موجودیت را با نام فارسی برای کاتالوگ UI می‌آورد."""
    columns = load_column_config()
    aliases = (load_entity_config().get("aliases") or {}).get("entity_type") or {}
    types = []
    for code in (columns.get("enums") or {}).get("entity_type") or []:
        names = aliases.get(code) or []
        if not isinstance(names, list):
            names = []
        types.append(
            {
                "code": str(code),
                "name": str(names[0]) if names else str(code),
                "aliases": [str(item) for item in names if str(item).strip()],
            }
        )
    return types


def catalog_payload() -> dict:
    """کاتالوگ و مثال‌های آماده را برای UI تست می‌دهد."""
    discourses = load_discourse_catalog()
    intents = load_intent_catalog()
    rhetorics = load_rhetoric_catalog()
    stance = load_stance_catalog()
    samples = [
        _sample_row(
            label="۹ نوع موجودیت",
            text=SAMPLE_TEXT,
            group="entity",
            note="متن ساختگی است؛ از دیتابیس نیامده. برای پوشش هر ۹ نوع نوشته شد.",
        )
    ]
    samples.extend(_accept_examples(discourses, "discourse"))
    samples.extend(_accept_examples(intents, "intent"))
    samples.extend(_accept_examples(rhetorics, "rhetoric"))
    for item in JOINT_EXAMPLES:
        samples.append(
            _sample_row(
                label=str(item.get("label") or item.get("note") or "ترکیبی"),
                text=str(item["text"]),
                group="joint",
                note=str(item.get("note") or ""),
                expected_discourse=str(item.get("expected_discourse") or ""),
                expected_intent=str(item.get("expected_intent") or ""),
                expected_rhetoric=str(item.get("expected_rhetoric") or ""),
            )
        )
    return {
        "layers": [
            {"id": "entities", "name": "موجودیت"},
            {"id": "keywords", "name": "کلمهٔ کلیدی"},
            {"id": "topics", "name": "موضوع"},
            {"id": "sentiment", "name": "احساس"},
            {"id": "discourse", "name": "ژانر"},
            {"id": "intent", "name": "نیت"},
            {"id": "rhetoric", "name": "بیان"},
        ],
        "groups": [
            {"id": "entity", "name": "موجودیت"},
            {"id": "discourse", "name": "ژانر"},
            {"id": "intent", "name": "نیت"},
            {"id": "rhetoric", "name": "بیان"},
            {"id": "joint", "name": "ترکیبی"},
        ],
        "entity_types": _entity_types(),
        "topics": load_topic_catalog(),
        "polarities": stance["polarities"],
        "intensity_levels": stance["intensity_levels"],
        "emotions": stance["emotions"],
        "discourses": [_option(item) for item in discourses],
        "intents": [_option(item) for item in intents],
        "rhetorics": [_option(item) for item in rhetorics],
        "samples": samples,
        "examples": samples,
        "joint_examples": list(JOINT_EXAMPLES),
    }


def _clean_expected(value) -> str | None:
    """انتظار خالی را بی‌اثر می‌کند."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def score_speech_layer(payload: dict, list_key: str, expected) -> dict:
    """کد اصلی لایه را با انتظار می‌سنجد و زمان ابزار را نگه می‌دارد."""
    expected_code = _clean_expected(expected)
    trace = payload.get("trace") if isinstance(payload.get("trace"), dict) else {}
    tool = payload.get("tool") or trace.get("name")
    duration_ms = trace.get("duration_ms")
    if payload.get("status") == "error":
        return {
            "ok": False if expected_code else None,
            "expected": expected_code,
            "got": None,
            "name": None,
            "slots": {},
            "mention_text": "",
            "confidence": None,
            "hits": [],
            "error": payload.get("message"),
            "message": payload.get("message"),
            "tool": tool,
            "duration_ms": duration_ms,
            "trace": trace or None,
        }
    hits = payload.get(list_key) or []
    if not isinstance(hits, list):
        hits = []
    primary = next((item for item in hits if item.get("is_primary")), None)
    if primary is None and hits:
        primary = hits[0]
    got = primary.get("code") if isinstance(primary, dict) else None
    name = primary.get("name") if isinstance(primary, dict) else None
    slots = primary.get("slots") if isinstance(primary, dict) else {}
    if not isinstance(slots, dict):
        slots = {}
    ok = None if expected_code is None else got == expected_code
    return {
        "ok": ok,
        "expected": expected_code,
        "got": got,
        "name": name,
        "slots": slots,
        "mention_text": (primary or {}).get("mention_text") or "",
        "confidence": (primary or {}).get("confidence"),
        "hits": hits,
        "error": None,
        "message": payload.get("message"),
        "tool": tool,
        "duration_ms": duration_ms,
        "trace": trace or None,
    }


def combine_check(
    text: str,
    discourse_payload: dict,
    intent_payload: dict,
    rhetoric_payload: dict,
    expected_discourse,
    expected_intent,
    expected_rhetoric,
    wall_ms: float,
) -> dict:
    """نتیجهٔ سه لایه را در یک پاسخ تست جمع می‌کند."""
    discourse = score_speech_layer(
        discourse_payload, "discourses", expected_discourse
    )
    intent = score_speech_layer(intent_payload, "intents", expected_intent)
    rhetoric = score_speech_layer(rhetoric_payload, "rhetorics", expected_rhetoric)
    if isinstance(rhetoric_payload, dict):
        rhetoric["intended_meaning"] = rhetoric_payload.get("intended_meaning") or ""
    judged = [
        item["ok"]
        for item in (discourse, intent, rhetoric)
        if item["ok"] is not None
    ]
    ok = all(judged) if judged else None
    return {
        "status": "success",
        "text": text,
        "ok": ok,
        "duration_ms": wall_ms,
        "discourse": discourse,
        "intent": intent,
        "rhetoric": rhetoric,
        "intended_meaning": rhetoric.get("intended_meaning") or "",
    }
