"""ایندکس تحلیل‌های بدون بردار. از ترمینال اجرا شود؛ heredoc لازم نیست."""

from paths import ensure_import_path

ensure_import_path()

from business_logic.config import load_llm_config
from business_logic.indexer import index_analysis
from business_logic.repository import fetch_pending_analysis_ids

ACTOR_ID = 216
LIMIT = 30


def main() -> None:
    cfg = load_llm_config()
    print("model:", cfg["embedding_model"], flush=True)
    print("key:", "ok" if cfg.get("api_key") else "MISSING", flush=True)
    ids = fetch_pending_analysis_ids(ACTOR_ID, cfg["embedding_model"], LIMIT)
    print(f"pending: {len(ids)}", flush=True)
    if not ids:
        print("چیزی برای امبد نمانده", flush=True)
        return
    ok = 0
    for index, analysis_id in enumerate(ids, 1):
        print(f"[{index}/{len(ids)}] analysis {analysis_id} ...", flush=True)
        try:
            stored = index_analysis(analysis_id, ACTOR_ID)
            ok += 1
            print(
                f"  cards={stored['indexed_count']} "
                f"{stored['source_type']}#{stored['source_id']}",
                flush=True,
            )
        except Exception as exc:
            print(f"  FAILED: {exc}", flush=True)
            return
    print(f"done {ok}/{len(ids)}", flush=True)


if __name__ == "__main__":
    main()
