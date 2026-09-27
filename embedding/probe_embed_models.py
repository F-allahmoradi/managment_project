"""کدام مدل امبدینگ روی همین کلید باز است. کلید را چاپ نمی‌کند."""

from paths import ensure_import_path

ensure_import_path()

import json
import urllib.error
import urllib.request

from business_logic.config import load_llm_config

_FALLBACK = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
    "text-embedding-v3",
    "text-embedding-v4",
    "gemini-embedding-001",
    "gemini-embedding-2",
    "embed-v-4-0",
    "cohere.embed-multilingual-v3",
    "cf.embeddinggemma-300m",
]


def _request(url: str, api_key: str, payload=None):
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _model_ids(base_url: str, api_key: str) -> list[str]:
    try:
        envelope = _request(f"{base_url}/models", api_key)
    except urllib.error.HTTPError:
        return list(_FALLBACK)
    ids = [str(item.get("id") or "") for item in (envelope.get("data") or [])]
    embed = [name for name in ids if "embed" in name.lower()]
    ordered = []
    for name in _FALLBACK + embed:
        if name and name not in ordered:
            ordered.append(name)
    return ordered


def main() -> None:
    cfg = load_llm_config()
    api_key = cfg.get("api_key") or ""
    if not api_key:
        print("key: MISSING", flush=True)
        return
    print("key: ok", flush=True)
    models = _model_ids(cfg["base_url"], api_key)
    print(f"candidates: {len(models)}", flush=True)
    found = []
    for model in models:
        try:
            body = _request(
                f"{cfg['base_url']}/embeddings",
                api_key,
                {"model": model, "input": ["سلام"]},
            )
            vector = ((body.get("data") or [{}])[0].get("embedding") or [])
            print(f"OK  {model}  dim={len(vector)}", flush=True)
            found.append(model)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            code = ""
            try:
                code = (json.loads(raw).get("error") or {}).get("code") or ""
            except json.JSONDecodeError:
                code = str(exc.code)
            print(f"NO  {model}  {exc.code} {code}", flush=True)
    print("usable:", ", ".join(found) if found else "none", flush=True)


if __name__ == "__main__":
    main()
