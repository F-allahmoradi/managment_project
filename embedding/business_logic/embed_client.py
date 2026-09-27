"""فراخوانی مدل امبدینگ OpenAI-compatible.

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

_BATCH = 32


def _post_embeddings(texts: list[str]) -> list[list[float]]:
    """یک دسته متن را به بردار تبدیل می‌کند."""
    settings = load_llm_config()
    model = str(settings.get("embedding_model") or "").strip()
    if not model:
        raise LlmError("نام مدل امبدینگ خالی است")
    url = f"{settings['base_url']}/embeddings"
    payload = {"model": model, "input": texts}
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    api_key = settings["api_key"]
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    timeout = int(settings.get("embedding_timeout_seconds") or settings["timeout_seconds"])
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status = exc.code
        if status in (401, 403):
            raise LlmError("احراز هویت مدل امبدینگ ناموفق بود") from exc
        raise LlmError("فراخوانی مدل امبدینگ ناموفق بود") from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise LlmError("زمان پاسخ مدل امبدینگ تمام شد") from exc
        raise LlmError("اتصال به سرویس مدل امبدینگ برقرار نشد") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise LlmError("زمان پاسخ مدل امبدینگ تمام شد") from exc
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmError("پاسخ سرویس امبدینگ JSON معتبر نیست") from exc
    rows = envelope.get("data") or []
    if not isinstance(rows, list) or len(rows) != len(texts):
        raise LlmError("تعداد بردار با تعداد متن یکی نیست")
    ordered = sorted(rows, key=lambda item: int((item or {}).get("index") or 0))
    vectors = []
    for item in ordered:
        vector = (item or {}).get("embedding")
        if not isinstance(vector, list) or not vector:
            raise LlmError("بردار امبدینگ خالی است")
        vectors.append([float(value) for value in vector])
    return vectors


@logged_step("embed")
def embed_texts(texts: list[str]) -> list[list[float]]:
    """متن‌ها را با مدل قفل‌شده به بردار تبدیل می‌کند.

    ورودی texts به لاگ یا استثنا کپی نمی‌شود.
    """
    cleaned = [str(item or "").strip() for item in texts]
    if any(not item for item in cleaned):
        raise LlmError("متن امبدینگ خالی است")
    vectors: list[list[float]] = []
    for start in range(0, len(cleaned), _BATCH):
        vectors.extend(_post_embeddings(cleaned[start : start + _BATCH]))
    if len(vectors) != len(cleaned):
        raise LlmError("تعداد بردار با تعداد متن یکی نیست")
    width = len(vectors[0])
    if any(len(item) != width for item in vectors):
        raise LlmError("طول بردارهای امبدینگ یکسان نیست")
    return vectors
