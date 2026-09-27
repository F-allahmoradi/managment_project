"""مسیر مشترک ابزارهای پردازش زبانی: اعتبارسنجی و خواندن منبع. INSERT نیست."""

from typing import Callable, Optional

from auth.gate import require_permission
from auth.principal import resolve_actor
from business_logic.repository import fetch_source_text
from errors.crud import format_error, format_success
from logging_module import logged_tool
from validators.extract import validate_extract_nlp

_SOURCE_PERMISSION = {
    "meeting": ("Meeting", "Read"),
    "message": ("Message", "Read"),
}


def make_extract_runner(tool_name: str, extract_fn: Callable) -> Callable:
    """اجراکنندهٔ مشترک یک لایه استخراج را می‌سازد."""

    @logged_tool(tool_name)
    def run(
        text: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        context: Optional[str] = None,
    ) -> dict:
        try:
            parsed = validate_extract_nlp(
                {
                    "text": text,
                    "source_type": source_type,
                    "source_id": source_id,
                    "context": context,
                }
            )
            resolved_type = parsed.get("source_type")
            resolved_id = parsed.get("source_id")
            body = parsed.get("text")
            extra_context = parsed.get("context")
            if resolved_type is not None and resolved_id is not None:
                resource_action = _SOURCE_PERMISSION.get(resolved_type)
                if resource_action is None:
                    actor = resolve_actor()
                else:
                    resource, action = resource_action
                    actor = require_permission(resource, action)
                source = fetch_source_text(resolved_type, resolved_id, actor["id"])
                body = source["text"]
            result = extract_fn(
                body,
                source_type=resolved_type,
                source_id=resolved_id,
                context=extra_context,
            )
            payload = result.model_dump(exclude={"status", "message"})
            return format_success(result.message, **payload)
        except Exception as exc:
            return format_error(exc)

    return run
