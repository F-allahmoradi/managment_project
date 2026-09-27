"""پایپ‌لاین استخراج متن پروژه. INSERT نیست.

هر لایه ابزار و درخواست مدل جدا دارد تا دقت بالا بماند.
تاریخ TIME از شاهد فارسی اینجا تبدیل می‌شود، نه از حدس مدل.
"""

from business_logic.config import (
    load_column_config,
    load_discourse_catalog,
    load_discourse_discovery,
    load_entity_config,
    load_intent_catalog,
    load_rhetoric_catalog,
    load_stance_catalog,
    load_topic_catalog,
    load_topic_discovery,
)
from business_logic.layers.discovery import persist_discovered_discourses
from business_logic.layers import (
    canonical_from_mentions,
    discourses_from_payload,
    emotions_from_payload,
    intents_from_payload,
    keywords_from_payload,
    mentions_from_payload,
    rhetorics_from_payload,
    sentiment_from_payload,
    topics_from_payload,
)
from business_logic.layers.topic import persist_discovered_topics
from business_logic.llm_client import complete_json
from business_logic.normalizer import normalize_text
from logging_module import logged_step
from schemas.output import (
    ExtractDiscourseOutput,
    ExtractEntitiesOutput,
    ExtractIntentOutput,
    ExtractKeywordsOutput,
    ExtractRhetoricOutput,
    ExtractSentimentOutput,
    ExtractTopicsOutput,
)

_SOURCE_KEY = "project_texts"


def _span_prompt() -> str:
    """دستور فقط برای ذکر موجودیت."""
    columns = load_column_config(_SOURCE_KEY)
    aliases = load_entity_config().get("aliases") or {}
    extractable = list((columns.get("enums") or {}).get("entity_type") or [])
    ranges = columns.get("ranges") or {}
    lines = [
        "You extract named entities from Persian (or mixed) project text.",
        "The text may be a report, meeting transcript, or message.",
        "Return JSON only, with this shape:",
        '{"mentions":[{"type":"<ENTITY_TYPE>","canonical_name":"<standard name>","mention_text":"<exact substring>","confidence":0.0}]}',
        "Rules:",
        "- Entity types only: " + ", ".join(extractable) + ".",
        "- Do not invent entity types. Do not output ACTION, keywords, topics, sentiment, discourse, or intent.",
        "- mention_text must be copied exactly from the user text. Do not paraphrase.",
        "- canonical_name is the standard name (full person name, org name, task title).",
        "- Omit a mention if it is not clearly stated. Do not guess.",
        "- Repeat the same entity once per distinct mention span.",
        "- ROLE is a job title (مدیر پروژه). PERSON is a named human.",
        "- UNIT is an internal team (واحد مالی). ORG is a company or contractor.",
        "- TASK is a specific work item, not a generic 'باید کار کنیم'.",
        "- TIME is a specific date or deadline. Copy the date span exactly; do not convert it.",
        "- OBJECT is equipment/material/system. PLACE is a location on site.",
        "- confidence is between 0 and 1. Use 0.9 or higher only when the span is copied exactly and the type is clear.",
    ]
    mapping = aliases.get("entity_type") or {}
    hints = []
    for canonical, words in mapping.items():
        joined = "، ".join(str(word) for word in (words or []))
        hints.append(f"{canonical} ← {joined}")
    if hints:
        lines.append("  hints: " + " ; ".join(hints))
    mention_range = ranges.get("mentions") or {}
    if "max" in mention_range:
        lines.append(f"- Return at most {mention_range['max']} mentions.")
    return "\n".join(lines)


def _keywords_prompt() -> str:
    """دستور فقط برای کلمهٔ کلیدی."""
    columns = load_column_config(_SOURCE_KEY)
    keyword_max = int(
        ((columns.get("ranges") or {}).get("keywords") or {}).get("max") or 12
    )
    return "\n".join(
        [
            "You extract short domain keywords from Persian (or mixed) project text.",
            "Return JSON only, with this shape:",
            '{"keywords":[{"phrase":"<short phrase>","mention_text":"<exact substring>","confidence":0.0}]}',
            "Rules:",
            "- Do not extract named entities (person, org, place, object, role, dates).",
            "- keywords are short domain phrases (1–5 words).",
            "- Prefer issue/theme phrases like تأخیر پرداخت or خرابی سرور.",
            "- mention_text must be copied exactly from the user text.",
            f"- Return at most {keyword_max} keywords.",
        ]
    )


def _topics_prompt() -> str:
    """دستور فقط برای درخت موضوع؛ هر گره مثل ژانر تعریف دارد."""
    columns = load_column_config(_SOURCE_KEY)
    catalog = load_topic_catalog()
    discovery = load_topic_discovery()
    topic_max = int(((columns.get("ranges") or {}).get("topics") or {}).get("max") or 8)
    lines = [
        "You classify the subject-matter (what the message or report is ABOUT).",
        "This is the domain tree, not discourse genre and not speaker intent.",
        "A complaint about late payment is still finance.payment.delay here; the complaint itself is intent/discourse elsewhere.",
        "Return JSON only, with this shape:",
        '{"topics":[{"code":"finance.payment.delay","is_primary":true,"mention_text":"<exact substring>","confidence":0.0}]}',
        "Rules:",
        "- Prefer catalog codes. A node is allowed only if its definition fits and its contrast rules do not send it elsewhere.",
        "- Prefer the most specific leaf. Do not stay at a parent when a child definition matches.",
        "- If several catalog nodes are truly present, keep at most "
        + str(topic_max)
        + " and set is_primary on the most specific dominant one.",
        "- management is fallback only: project coordination, orders, resolutions. Never dump unrelated text into it.",
        "- Never return an empty topics array. Every utterance has a subject.",
        "- mention_text must be copied exactly from the user text.",
        "- Do not extract named entities, keywords, sentiment, discourse, or intent here.",
        "- Codes:",
    ]
    lines.extend(_catalog_prompt_lines(catalog))
    if discovery.get("enabled"):
        lines.extend(
            [
                "Open discovery:",
                "- If NO catalog node fits the text, do NOT force a nearby code, do NOT use management as a dump, and do NOT return [].",
                "- Name the actual subject of the utterance or report: a short Persian name (2–6 words), English snake_case code, and a one-line definition grounded in the text.",
                "- Emit it with discovered=true. mention_text must be an exact substring of the user text.",
                "- Do not invent a synonym of a catalog node.",
                "- JSON for a discovered topic:",
                '{"topics":[{"code":"parenting","name":"تربیت فرزند","discovered":true,"definition":"آموزش و حدگذاری برای رفتار فرزند","is_primary":true,"mention_text":"تربیت فرزند","confidence":0.8}]}',
            ]
        )
        for rule in discovery.get("rules") or []:
            lines.append(f"    - {rule}")
    return "\n".join(lines)


def _sentiment_prompt(intended_meaning: str | None = None) -> str:
    """دستور فقط برای قطبیت و هیجان."""
    columns = load_column_config(_SOURCE_KEY)
    stance = load_stance_catalog()
    polarities = ", ".join(item["code"] for item in stance["polarities"])
    intensities = ", ".join(item["code"] for item in stance["intensity_levels"])
    emotions = ", ".join(f"{item['code']}={item['name']}" for item in stance["emotions"])
    emotion_max = int(
        ((columns.get("ranges") or {}).get("emotions") or {}).get("max") or 3
    )
    lines = [
        "You classify stance of Persian (or mixed) project text.",
        "Return JSON only, with this shape:",
        '{"sentiment":{"polarity":"negative","intensity":"medium","mention_text":"<exact substring>","confidence":0.0},"emotions":[{"emotion":"worry","intensity":"medium","mention_text":"<exact substring>","confidence":0.0}]}',
        "Rules:",
        f"- sentiment.polarity is overall document polarity: {polarities}.",
        f"- sentiment.intensity is {intensities}.",
        "- If the text mixes facts and complaints, pick the dominant polarity.",
        "- Classify intended polarity, not surface praise. Ironic 'عالی' with a failure is negative.",
        f"- emotions use ONLY these codes: {emotions}.",
        f"- Return at most {emotion_max} emotions. Emotion is not the same as polarity.",
        "- mention_text must be copied exactly from the user text.",
        "- Omit sentiment or emotions if the text has no clear stance.",
        "- Do not extract named entities, topics, discourse, or intent.",
    ]
    lines.extend(_intended_meaning_lines(intended_meaning))
    return "\n".join(lines)


def _slot_prompt_lines(label: str, slots: list[dict]) -> list[str]:
    """نقش‌ها را با توضیح کنار نام برای مدل می‌چیند."""
    if not slots:
        return []
    lines = [f"    {label}:"]
    for slot in slots:
        name = str(slot.get("name") or "").strip()
        if not name:
            continue
        note = str(slot.get("description") or "").strip()
        lines.append(f"      - {name}: {note}" if note else f"      - {name}")
    return lines


def _catalog_prompt_lines(catalog: list[dict]) -> list[str]:
    """تعریف نقش‌دار یک کاتالوگ بسته را برای مدل می‌چیند."""
    lines: list[str] = []
    for item in catalog:
        flags = []
        if item.get("fallback"):
            flags.append("fallback")
        if item.get("discovered"):
            flags.append("discovered")
        suffix = f", {', '.join(flags)}" if flags else ""
        if "priority" in item:
            head = f"priority {item['priority']}{suffix}"
        else:
            parent = item.get("parent_code") or "root"
            head = f"level {item.get('level') or 1}, parent {parent}{suffix}"
        lines.append(f"  {item['code']} = {item['name']} ({head})")
        definition = str(item.get("definition") or "").strip()
        if definition:
            lines.append(f"    definition: {definition}")
        description = str(item.get("description") or "").strip()
        if description:
            lines.append(f"    description: {description}")
        lines.extend(_slot_prompt_lines("required slots", item.get("required_slots") or []))
        lines.extend(_slot_prompt_lines("optional slots", item.get("optional_slots") or []))
        for rule in item.get("contrast") or []:
            lines.append(f"    not: {rule}")
        if item.get("accept_example"):
            lines.append(f"    yes: {item['accept_example']}")
        if item.get("reject_example"):
            lines.append(f"    no: {item['reject_example']}")
        cues = item.get("cues") or []
        if cues:
            lines.append(f"    signals: {', '.join(cues)}")
    return lines


def _intended_meaning_lines(intended_meaning: str | None) -> list[str]:
    """قواعد غیرصریح یا بازنویسیٔ آماده را به پرامپت لایه می‌چسباند."""
    meaning = str(intended_meaning or "").strip()
    if meaning:
        return [
            "- Classify from this intended-meaning rewrite, not from surface politeness or praise.",
            "- mention_text and slot values must still be exact substrings of the original user text.",
            f"- Intended meaning: {meaning}",
        ]
    return [
        "- Classify from the speaker's intended meaning, not surface praise, politeness, or jokes.",
        "- Irony/sarcasm often uses positive words (عالی، آفرین، دست مریزاد، شاهکار) for a negative complaint or objection.",
        "- A rhetorical question is not a request for information if no answer is expected.",
        "- Metaphor and humor do not change the handling path: an ironic objection is still an objection.",
        "- Required slots may be filled from implied meaning; mention_text must still be an exact substring of the original user text.",
    ]


def _discourses_prompt(intended_meaning: str | None = None) -> str:
    """دستور فقط برای ژانر / نوع پیام."""
    columns = load_column_config(_SOURCE_KEY)
    catalog = load_discourse_catalog()
    discovery = load_discourse_discovery()
    max_hits = int(
        ((columns.get("ranges") or {}).get("discourses") or {}).get("max") or 3
    )
    lines = [
        "You classify the discourse genre (message type) of Persian (or mixed) project text.",
        "This is the form of the utterance, not the speaker's goal and not sentiment.",
        "Return JSON only, with this shape:",
        '{"discourses":[{"code":"<discourse code>","is_primary":true,"mention_text":"<exact substring>","confidence":0.0,"slots":{"<slot>":"<value from text>"}}]}',
        "Rules:",
        "- Prefer these catalog codes. A catalog label is allowed only if every required slot is filled from the text.",
        "- If several labels fit, keep at most "
        + str(max_hits)
        + " and set is_primary on the highest priority.",
        "- Exactly one item must have is_primary true.",
        "- message is fallback only. Do not choose it when another required-slot frame fits.",
        "- Do not classify intent, topics, entities, sentiment, or rhetoric here.",
        "- mention_text must be copied exactly from the user text.",
        "- slots are the filled required roles with short spans from the text.",
        "- A rhetorical question is not discourse question if no answer is expected.",
        "- Irony and humor are not a genre; pick the real frame (issue, feedback, request).",
        "- Codes:",
    ]
    lines.extend(_catalog_prompt_lines(catalog))
    lines.extend(_intended_meaning_lines(intended_meaning))
    if discovery.get("enabled"):
        min_slots = int(discovery.get("min_required_slots") or 2)
        lines.extend(
            [
                "Open discovery:",
                "- If NO catalog frame except message has all required slots filled from the text, but the utterance is a distinct repeatable speech act, do NOT force it into a nearby catalog code and do NOT drop it.",
                "- Emit it as a new discourse with discovered=true, its own English snake_case code, Persian name, definition, required_slots, optional_slots, and slots filled from the text.",
                f"- A new type needs at least {min_slots} required slots whose values are exact substrings of the user text.",
                "- Do not invent a synonym of a catalog type. Do not use message when a structured new type fits.",
                "- Greeting or empty chit-chat is still message, not a new type.",
                "- JSON for a discovered type:",
                '{"discourses":[{"code":"commitment","name":"تعهد","discovered":true,"definition":"...","is_primary":true,"mention_text":"<exact substring>","confidence":0.8,"required_slots":[{"name":"...","description":"..."}],"optional_slots":[],"slots":{"<slot>":"<exact substring>"}}]}',
            ]
        )
        for rule in discovery.get("rules") or []:
            lines.append(f"    - {rule}")
    return "\n".join(lines)


def _intents_prompt(intended_meaning: str | None = None) -> str:
    """دستور فقط برای نیت / مسیر رسیدگی."""
    columns = load_column_config(_SOURCE_KEY)
    catalog = load_intent_catalog()
    max_hits = int(((columns.get("ranges") or {}).get("intents") or {}).get("max") or 2)
    lines = [
        "You classify the speaker intent (desired next action) of Persian (or mixed) project text.",
        "This is the goal after reading, not the discourse genre and not sentiment.",
        "A problem-shaped text may be report_problem, request_action, follow_up, or complaint.",
        "Return JSON only, with this shape:",
        '{"intents":[{"code":"<intent code>","is_primary":true,"mention_text":"<exact substring>","confidence":0.0,"slots":{"<slot>":"<value from text>"}}]}',
        "Rules:",
        "- Use ONLY these codes. A label is allowed only if every required slot is filled from the text.",
        "- If several labels fit, keep at most "
        + str(max_hits)
        + " and set is_primary on the highest priority.",
        "- Exactly one item must have is_primary true.",
        "- inform is fallback only. Do not choose it when another required-slot frame fits.",
        "- Do not output question, answer, suggestion, or warning; those are discourse codes.",
        "- Do not classify discourse, topics, entities, sentiment, or rhetoric here.",
        "- mention_text must be copied exactly from the user text.",
        "- slots are the filled required roles with short spans from the text.",
        "- Codes:",
    ]
    lines.extend(_catalog_prompt_lines(catalog))
    lines.extend(_intended_meaning_lines(intended_meaning))
    return "\n".join(lines)


def _rhetorics_prompt() -> str:
    """دستور فقط برای صنعت بیان / لحن غیرصریح."""
    columns = load_column_config(_SOURCE_KEY)
    catalog = load_rhetoric_catalog()
    max_hits = int(
        ((columns.get("ranges") or {}).get("rhetorics") or {}).get("max") or 2
    )
    lines = [
        "You classify the rhetorical device of Persian (or mixed) project text.",
        "This is HOW the speaker talks, not the handling path and not the discourse genre.",
        "An ironic objection is still an objection elsewhere; here you only label the device.",
        "Return JSON only, with this shape:",
        '{"rhetorics":[{"code":"<rhetoric code>","is_primary":true,"mention_text":"<exact substring>","confidence":0.0,"slots":{"<slot>":"<value from text>"}}],"intended_meaning":"<literal Persian rewrite of what the speaker actually means>"}',
        "Rules:",
        "- Use ONLY these codes. A label is allowed only if every required slot is filled from the text.",
        "- If several labels fit, keep at most "
        + str(max_hits)
        + " and set is_primary on the highest priority.",
        "- Exactly one item must have is_primary true.",
        "- literal is fallback only. Do not choose it when another required-slot frame fits.",
        "- Do not classify intent, discourse, topics, entities, or sentiment here.",
        "- mention_text must be copied exactly from the user text.",
        "- slots are the filled required roles with short spans from the text.",
        "- intended_meaning is a short explicit Persian rewrite of the speaker's real goal or complaint.",
        "- If the text is literal, intended_meaning may repeat the text.",
        "- Positive words with a failure (چه عالی + قطع شد) are irony or sarcasm, not literal praise.",
        "- Codes:",
    ]
    lines.extend(_catalog_prompt_lines(catalog))
    return "\n".join(lines)


def _normalized(text: str) -> tuple[dict, str]:
    """ستون منبع و متن نرمال را آماده می‌کند."""
    return load_column_config(_SOURCE_KEY), normalize_text(text)


@logged_step("extract")
def extract_entities(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
) -> ExtractEntitiesOutput:
    """فقط موجودیت نام‌دار را استخراج می‌کند. INSERT نیست."""
    columns, normalized = _normalized(text)
    payload = complete_json(_span_prompt(), normalized)
    mentions = mentions_from_payload(payload, normalized)
    entities = canonical_from_mentions(mentions)
    type_counts: dict[str, int] = {}
    for mention in mentions:
        type_counts[mention.type] = type_counts.get(mention.type, 0) + 1
    count = len(mentions)
    return ExtractEntitiesOutput(
        status="success",
        message=f"{count} ذکر موجودیت استخراج شد",
        source=_SOURCE_KEY,
        table=str(columns.get("table") or "entity_mentions"),
        column=str(columns.get("column") or "mention_text"),
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        extracted_count=count,
        canonical_count=len(entities),
        type_counts=type_counts,
        entities=entities,
        mentions=mentions,
    )


@logged_step("extract")
def extract_keywords(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
) -> ExtractKeywordsOutput:
    """فقط کلمهٔ کلیدی آزاد را استخراج می‌کند. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_keywords_prompt(), normalized)
    keywords = keywords_from_payload(payload, normalized)
    return ExtractKeywordsOutput(
        status="success",
        message=f"{len(keywords)} کلمهٔ کلیدی استخراج شد",
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        keywords=keywords,
        keyword_count=len(keywords),
    )


@logged_step("extract")
def extract_topics(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
) -> ExtractTopicsOutput:
    """موضوع کاتالوگ یا موضوع فهمیده‌شدهٔ خارج از درخت را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_topics_prompt(), normalized)
    topics = topics_from_payload(payload, normalized)
    try:
        persist_discovered_topics(topics)
    except OSError:
        pass
    if topics:
        primary = next(item for item in topics if item.is_primary)
        if primary.discovered:
            message = (
                f"موضوع «{primary.name}» از متن فهمیده شد (در درخت حوزه نبود)"
            )
        elif len(topics) == 1:
            message = f"موضوع {primary.name} استخراج شد"
        else:
            message = f"{len(topics)} موضوع استخراج شد"
    else:
        message = "موضوعی استخراج نشد"
    return ExtractTopicsOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        topics=topics,
        topic_count=len(topics),
    )


@logged_step("extract")
def extract_sentiment(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    intended_meaning: str | None = None,
) -> ExtractSentimentOutput:
    """فقط قطبیت و هیجان را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_sentiment_prompt(intended_meaning), normalized)
    sentiment = sentiment_from_payload(payload, normalized)
    emotions = emotions_from_payload(payload, normalized)
    parts = []
    if sentiment is not None:
        parts.append(f"احساس {sentiment.polarity_name}")
    if emotions:
        parts.append(f"{len(emotions)} هیجان")
    message = " و ".join(parts) + " استخراج شد" if parts else "احساسی استخراج نشد"
    return ExtractSentimentOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        sentiment=sentiment,
        emotions=emotions,
        emotion_count=len(emotions),
    )


@logged_step("extract")
def extract_discourse(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    intended_meaning: str | None = None,
) -> ExtractDiscourseOutput:
    """فقط ژانر / نوع پیام را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_discourses_prompt(intended_meaning), normalized)
    discourses = discourses_from_payload(payload, normalized)
    try:
        persist_discovered_discourses(discourses)
    except OSError:
        pass
    if discourses:
        primary = next(item for item in discourses if item.is_primary)
        suffix = " (نوع کشف‌شده)" if primary.discovered else ""
        message = f"ژانر {primary.name} استخراج شد{suffix}"
    else:
        message = "ژانری استخراج نشد"
    return ExtractDiscourseOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        discourses=discourses,
        discourse_count=len(discourses),
    )


@logged_step("extract")
def extract_intent(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
    intended_meaning: str | None = None,
) -> ExtractIntentOutput:
    """فقط نیت گوینده را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_intents_prompt(intended_meaning), normalized)
    intents = intents_from_payload(payload, normalized)
    if intents:
        primary = next(item for item in intents if item.is_primary)
        message = f"نیت {primary.name} استخراج شد"
    else:
        message = "نیتی استخراج نشد"
    return ExtractIntentOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        intents=intents,
        intent_count=len(intents),
    )


@logged_step("extract")
def extract_rhetoric(
    text: str,
    *,
    source_type: str | None = None,
    source_id: int | None = None,
) -> ExtractRhetoricOutput:
    """فقط صنعت بیان و معنای مقصود را برمی‌دارد. INSERT نیست."""
    _columns, normalized = _normalized(text)
    payload = complete_json(_rhetorics_prompt(), normalized)
    rhetorics, intended_meaning = rhetorics_from_payload(payload, normalized)
    if rhetorics:
        primary = next(item for item in rhetorics if item.is_primary)
        message = f"بیان {primary.name} استخراج شد"
    else:
        message = "بیانی استخراج نشد"
    return ExtractRhetoricOutput(
        status="success",
        message=message,
        source=_SOURCE_KEY,
        source_type=source_type,
        source_id=source_id,
        text_length=len(normalized),
        rhetorics=rhetorics,
        rhetoric_count=len(rhetorics),
        intended_meaning=intended_meaning,
    )
