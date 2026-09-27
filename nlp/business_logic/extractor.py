"""پایپ‌لاین فکت، نقل‌قول و قاب مسئله. INSERT نیست.

هر لایه درخواست مدل جدا دارد. عددِ نیامده در متن فقط با حساب منابع صریح می‌ماند.
"""

from business_logic.config import (
    load_column_config,
    load_facts_catalog,
    load_frames_catalog,
    load_quotes_catalog,
)
from business_logic.derive import document_explicitness
from business_logic.layers import (
    facts_from_payload,
    frame_from_payload,
    quotes_from_payload,
)
from business_logic.llm_client import complete_json
from business_logic.normalizer import normalize_text
from logging_module import logged_step
from schemas.output import ExtractFactsOutput, ExtractFrameOutput, ExtractQuotesOutput

_SOURCE_KEY = "project_texts"


def _normalized(text: str) -> tuple[dict, str]:
    """ستون منبع و متن نرمال را آماده می‌کند."""
    return load_column_config(_SOURCE_KEY), normalize_text(text)


def _context_lines(context: str | None) -> list[str]:
    """بافت اختیاری را به پرامپت می‌چسباند؛ شاهد همچنان از متن اصلی است."""
    body = str(context or "").strip()
    if not body:
        return []
    return [
        "- Optional prior/next context follows in the user message after CONTEXT:.",
        "- Use context only to resolve pronouns. mention_text and quoted_text must still be exact substrings of the main TEXT.",
    ]


def _user_payload(text: str, context: str | None) -> str:
    """متن اصلی و بافت را برای مدل می‌چیند."""
    body = str(text or "").strip()
    extra = str(context or "").strip()
    if extra:
        return f"CONTEXT:\n{extra}\n\nTEXT:\n{body}"
    return body


def _facts_prompt(context: str | None = None) -> str:
    """دستور فقط برای فکت و صراحت."""
    columns = load_column_config(_SOURCE_KEY)
    catalog = load_facts_catalog()
    fact_max = int(((columns.get("ranges") or {}).get("facts") or {}).get("max") or 24)
    kinds = ", ".join(f"{item['code']}={item['name']}" for item in catalog["kinds"])
    units = ", ".join(item["code"] for item in catalog["units"])
    groundings = ", ".join(item["code"] for item in catalog["groundings"])
    roles = ", ".join(item["code"] for item in catalog["quantity_roles"])
    derivations = ", ".join(item["code"] for item in catalog["derivations"])
    lines = [
        "You extract grounded facts from Persian (or mixed) project text.",
        "This is NOT intent, discourse, sentiment, or named-entity typing.",
        "Return JSON only, with this shape:",
        '{"facts":[{"id":"q1","kind":"quantity","name":"...","value":30,"unit":"percent","role":"total","grounding":"explicit","mention_text":"<exact substring>","confidence":0.9,"source_ids":[],"derivation":"","effect":"","previous":"","current":"","evidence_texts":[]}]}',
        "Rules:",
        f"- kind ONLY: {kinds}.",
        f"- unit ONLY when kind is quantity: {units}.",
        f"- grounding ONLY: {groundings}. Never invent a third code.",
        f"- role for quantities: {roles}.",
        f"- derivation for derived numeric facts: {derivations}.",
        "- mention_text must be copied exactly from the TEXT.",
        "- explicit quantity: the number itself MUST appear in mention_text.",
        "- derived quantity: the number may be absent from the text, but source_ids must point to explicit quantity facts and the arithmetic must hold.",
        "- subtract/remainder: value = first source minus the other sources.",
        "- add: value = sum of sources.",
        "- Do not guess hidden motives. If a cause is not in the text, omit it.",
        "- Example: '۳۰ درصد کاهش' and '۱۰ درصد مربوط به بازاریابی' and cause 'کمبود نیروی متخصص' in the same sentence → derived remainder 20 with subtract of those two quantities.",
        "- Do not extract PERSON/ORG types. Do not classify complaint vs request.",
        f"- Return at most {fact_max} facts.",
    ]
    for rule in catalog.get("rules") or []:
        lines.append(f"- {rule}")
    lines.extend(_context_lines(context))
    return "\n".join(lines)


def _quotes_prompt(context: str | None = None) -> str:
    """دستور فقط برای نقل‌قول."""
    catalog = load_quotes_catalog()
    columns = load_column_config(_SOURCE_KEY)
    quote_max = int(
        ((columns.get("ranges") or {}).get("quotes") or {}).get("max") or 8
    )
    modes = ", ".join(f"{item['code']}={item['name']}" for item in catalog["modes"])
    lines = [
        "You extract quoted or reported speech from Persian (or mixed) project text.",
        "The message sender may differ from the inner speaker.",
        "Return JSON only, with this shape:",
        '{"quotes":[{"mode":"indirect","attributed_to":"<exact substring>","quoted_text":"<exact substring>","mention_text":"<exact substring>","confidence":0.9}]}',
        "Rules:",
        f"- mode ONLY: {modes}.",
        "- attributed_to, quoted_text, and mention_text must be exact substrings of TEXT.",
        "- indirect: گزارش سخن دیگری مثل «رفتم واحد مالی گفت».",
        "- direct: گیومه یا نقل نزدیک.",
        "- If the speaker is only the message author and nothing is attributed to someone else, return {\"quotes\":[]}.",
        f"- Return at most {quote_max} quotes.",
    ]
    for rule in catalog.get("rules") or []:
        lines.append(f"- {rule}")
    lines.extend(_context_lines(context))
    return "\n".join(lines)


def _frame_prompt(context: str | None = None) -> str:
    """دستور فقط برای قاب مسئله."""
    catalog = load_frames_catalog()
    scopes = ", ".join(f"{item['code']}={item['name']}" for item in catalog["scopes"])
    processes = ", ".join(
        f"{item['code']}={item['name']}" for item in catalog["processes"]
    )
    lines = [
        "You build a compact issue frame from Persian (or mixed) project text.",
        "This is a card for later issues table, not intent classification.",
        "Return JSON only, with this shape:",
        '{"frame":{"title":"<short Persian title>","unit":"<exact substring or empty>","process":"staffing","scope":"organizational","about":"<exact substring>","confidence":0.8}}',
        "Rules:",
        f"- scope ONLY: {scopes}.",
        f"- process ONLY: {processes}.",
        "- title may be a short paraphrase.",
        "- unit and about must be exact substrings of TEXT, or empty.",
        "- If the text is greetings with no issue, return {\"frame\": null}.",
        "- Do not output intent codes like complaint.",
    ]
    for rule in catalog.get("rules") or []:
        lines.append(f"- {rule}")
    lines.extend(_context_lines(context))
    return "\n".join(lines)


@logged_step("extract")
def extract_facts(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    context: str | None = None,
) -> ExtractFactsOutput:
    """فکت عددی، شرط، علت، تغییر و وضعیت را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_facts_prompt(context), _user_payload(normalized, context))
    facts, dropped = facts_from_payload(payload, normalized)
    code, name = document_explicitness(facts)
    if facts:
        message = f"{len(facts)} فکت استخراج شد"
    else:
        message = "فکتی استخراج نشد"
    if dropped:
        message += f"؛ {dropped} ادعا بدون شاهد حذف شد"
    return ExtractFactsOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        explicitness=code,
        explicitness_name=name,
        facts=facts,
        fact_count=len(facts),
        dropped_count=dropped,
    )


@logged_step("extract")
def extract_quotes(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    context: str | None = None,
) -> ExtractQuotesOutput:
    """نقل‌قول مستقیم و غیرمستقیم را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_quotes_prompt(context), _user_payload(normalized, context))
    quotes = quotes_from_payload(payload, normalized)
    if quotes:
        message = f"{len(quotes)} نقل‌قول استخراج شد"
    else:
        message = "نقل‌قولی استخراج نشد"
    return ExtractQuotesOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        quotes=quotes,
        quote_count=len(quotes),
    )


@logged_step("extract")
def extract_frame(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    context: str | None = None,
) -> ExtractFrameOutput:
    """عنوان، واحد، فرآیند و محدوده مسئله را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_frame_prompt(context), _user_payload(normalized, context))
    frame = frame_from_payload(payload, normalized)
    if frame is None:
        message = "قاب مسئله استخراج نشد"
    else:
        message = f"قاب مسئله «{frame.title}» استخراج شد"
    return ExtractFrameOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        frame=frame,
    )
