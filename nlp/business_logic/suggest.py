"""عنوان کوتاه وظیفهٔ پیشنهادی از نیت NER یا قاب مسئله.

INSERT نیست. ذخیره با create_task و link_issue_task است.
"""

from typing import Any

_LACK_PREFIXES = ("کمبود ", "نبود ", "فقدان ", "عدم ")
_ACTION_SLOTS = {
    "request_action": "عمل مطلوب",
    "complaint": "خواسته",
    "follow_up": "مورد باز",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_dict(item: Any) -> dict:
    if item is None:
        return {}
    if isinstance(item, dict):
        return item
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        return dump()
    return {}


def _strip_lack(text: str) -> str:
    """پیشوند کمبود را برمی‌دارد تا عنوان کار ایجابی شود."""
    for prefix in _LACK_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def _from_intent(intents: Any) -> str:
    """از extract_intent همان عمل مطلوب را برمی‌دارد."""
    rows = intents or []
    if not isinstance(rows, list):
        return ""
    packed = [_as_dict(item) for item in rows]
    packed = [item for item in packed if item]
    if not packed:
        return ""
    primary = next((item for item in packed if item.get("is_primary")), packed[0])
    code = _clean(primary.get("code"))
    slots = primary.get("slots") if isinstance(primary.get("slots"), dict) else {}
    slot_name = _ACTION_SLOTS.get(code)
    if slot_name:
        return _clean(slots.get(slot_name))
    return ""


def _from_frame(frame: Any, facts: Any) -> str:
    """از قاب مسئله و در صورت نیاز فکت علت، عنوان کار می‌سازد."""
    packed = _as_dict(frame)
    if not packed:
        return ""
    process = _clean(packed.get("process"))
    process_name = _clean(packed.get("process_name"))
    about = _clean(packed.get("about"))
    unit = _clean(packed.get("unit"))
    if not about:
        for item in facts or []:
            fact = _as_dict(item)
            if fact.get("kind") == "cause":
                about = _clean(fact.get("name") or fact.get("mention_text"))
                if about:
                    break
    obj = _strip_lack(about)
    if process == "staffing" or process_name == "تأمین نیرو":
        if obj.startswith("نیرو"):
            action = f"تأمین {obj}"
        elif obj:
            action = f"تأمین {obj}"
        else:
            action = process_name or "تأمین نیرو"
    elif process_name and obj:
        action = f"{process_name} {obj}"
    else:
        action = process_name or obj
    if unit and unit not in action:
        action = f"{action} {unit}".strip()
    return action.strip()


def suggest_task_title(
    *,
    intents: Any = None,
    frame: Any = None,
    facts: Any = None,
) -> dict | None:
    """عنوان پیشنهادی وظیفه را از نیت یا متن مسئله برمی‌گرداند."""
    title = _from_intent(intents)
    source = "intent"
    if not title:
        title = _from_frame(frame, facts)
        source = "frame"
    if not title:
        return None
    return {"title": title[:200], "source": source}
