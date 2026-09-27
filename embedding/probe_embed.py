"""یک درخواست امبدینگ آزمایشی. کلید را چاپ نمی‌کند."""

from paths import ensure_import_path

ensure_import_path()

import json
import urllib.error
import urllib.request

from business_logic.config import load_llm_config


def main() -> None:
    cfg = load_llm_config()
    model = cfg["embedding_model"]
    url = f"{cfg['base_url']}/embeddings"
    print("url:", url, flush=True)
    print("model:", model, flush=True)
    print("key:", "ok" if cfg.get("api_key") else "MISSING", flush=True)
    payload = json.dumps({"model": model, "input": ["سلام"]}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        vector = ((body.get("data") or [{}])[0].get("embedding") or [])
        print("status: 200", flush=True)
        print("dim:", len(vector), flush=True)
        print("OK", flush=True)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print("status:", exc.code, flush=True)
        try:
            err = json.loads(raw).get("error") or {}
            print("code:", err.get("code"), flush=True)
            print("message:", err.get("message"), flush=True)
        except json.JSONDecodeError:
            print("body:", raw[:400], flush=True)


if __name__ == "__main__":
    main()
