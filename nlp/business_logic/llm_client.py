"""فراخوانی مدل زبانی OpenAI-compatible برای JSON ساخت‌یافته.

کلید API از محیط می‌آید؛ در لاگ و خطا نوشته نمی‌شود.
متن خام به لاگر نمی‌رود.
"""

import json
import socket
import urllib.error
import urllib.request

from business_logic.config import load_llm_config
from errors.crud import LlmError
from logging_module import logged_step


def _parse_json_content(raw: str) -> dict:
    """متن مدل را به دیکشنری JSON تبدیل می‌کند."""
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError("پاسخ مدل زبانی JSON معتبر نیست") from exc
    if not isinstance(loaded, dict):
        raise LlmError("پاسخ مدل زبانی باید یک شیء JSON باشد")
    return loaded


@logged_step("llm")
def complete_json(system: str, user: str) -> dict:
    """یک درخواست chat می‌فرستد و شیء JSON برمی‌گرداند.

    ورودی user همان متن است و در استثنا یا لاگ کپی نمی‌شود.
    """
    settings = load_llm_config()
    url = f"{settings['base_url']}/chat/completions"
    payload: dict = {
        "model": settings["model"],
        "temperature": settings["temperature"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if settings["json_response_format"]:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    api_key = settings["api_key"]
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(
            request,
            timeout=settings["timeout_seconds"],
        ) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status = exc.code
        if status in (401, 403):
            raise LlmError("احراز هویت مدل زبانی ناموفق بود") from exc
        raise LlmError("فراخوانی مدل زبانی ناموفق بود") from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise LlmError("زمان پاسخ مدل زبانی تمام شد") from exc
        raise LlmError("اتصال به سرویس مدل زبانی برقرار نشد") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise LlmError("زمان پاسخ مدل زبانی تمام شد") from exc
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmError("پاسخ سرویس مدل زبانی JSON معتبر نیست") from exc
    choices = envelope.get("choices") or []
    if not choices:
        raise LlmError("مدل زبانی هیچ انتخابی برنگرداند")
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlmError("محتوای پاسخ مدل زبانی خالی است")
    return _parse_json_content(content)
