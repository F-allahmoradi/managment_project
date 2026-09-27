"""لایه topic: طبقه‌بندی روی درخت حوزه.

جدول هدف: text_analysis_topics. برگ کاتالوگ یا موضوع کشف‌شده از متن.
"""

from pathlib import Path
from typing import Any
import hashlib
import re

import yaml

from business_logic.config import (
    discovered_topic_path,
    load_column_config,
    load_topic_catalog,
    load_topic_discovery,
)
from business_logic.normalizer import clean_text, find_span
from business_logic.validator import accept_confidence
from schemas.output import TopicHit

_SOURCE_KEY = "project_texts"
_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,78}$")
_INVENTED_CODES = {
    "contractor": "procurement",
    "operations": "management",
    "infrastructure": "tech",
    "delay": "finance.payment.delay",
    "issue": "management",
    "complaint": "management",
}


def topic_path(code: str, catalog: dict[str, dict]) -> tuple[list[str], list[str]]:
    """مسیر ریشه تا برگ را از کد نقطه‌ای می‌سازد."""
    parts = code.split(".")
    names: list[str] = []
    codes: list[str] = []
    for index in range(len(parts)):
        prefix = ".".join(parts[: index + 1])
        meta = catalog.get(prefix)
        if meta is None:
            continue
        codes.append(prefix)
        names.append(str(meta["name"]))
    return names, codes


def _norm_code(value: str) -> str:
    """کد مدل را برای تطبیق با کاتالوگ یکدست می‌کند."""
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("-", ".")
        .replace("/", ".")
        .replace(" ", ".")
    )


def resolve_topic_code(
    raw: str,
    catalog: dict[str, dict],
    name_hint: str = "",
) -> str | None:
    """کد یا نام مدل را به کد seed می‌رساند؛ کد نو را دور می‌ریزد."""
    code = _norm_code(raw)
    hint = str(name_hint or "").strip()
    mapped = _INVENTED_CODES.get(code)
    if mapped and mapped in catalog:
        code = mapped
    if code in catalog:
        return code
    for item in catalog.values():
        aliases = item.get("aliases") or []
        if code and code in {_norm_code(alias) for alias in aliases}:
            return str(item["code"])
        if hint and (hint == item["name"] or hint in aliases):
            return str(item["code"])
        if raw.strip() == item["name"]:
            return str(item["code"])
    last = code.split(".")[-1] if code else ""
    suffix_hits = [
        item_code
        for item_code in catalog
        if last and (item_code == last or item_code.endswith("." + last))
    ]
    if suffix_hits:
        return max(suffix_hits, key=lambda item_code: (item_code.count("."), len(item_code)))
    parts = code.split(".") if code else []
    for index in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:index])
        if prefix in catalog:
            return prefix
    return None


def _hit_from_meta(
    meta: dict,
    catalog: dict[str, dict],
    *,
    is_primary: bool,
    mention: str,
    confidence: float,
    normalized: str,
) -> TopicHit:
    """یک ردیف کاتالوگ را به TopicHit تبدیل می‌کند."""
    span = find_span(normalized, mention) if mention else None
    if span is None:
        mention = str(meta["name"])
        span = find_span(normalized, mention)
    if span is not None:
        mention = normalized[span[0] : span[1]]
    names, codes = topic_path(str(meta["code"]), catalog)
    return TopicHit(
        code=str(meta["code"]),
        name=str(meta["name"]),
        level=int(meta["level"]),
        parent_code=meta.get("parent_code"),
        path=names,
        path_codes=codes,
        is_primary=bool(is_primary),
        mention_text=mention,
        confidence=accept_confidence(confidence),
        discovered=bool(meta.get("discovered")),
        definition=str(meta.get("definition") or "").strip() or None,
    )


def _has_topic_evidence(meta: dict, normalized: str) -> bool:
    """برای موضوع پیش‌فرض، بدون شاهد داخل متن قبول نمی‌کند."""
    needles = [str(meta.get("name") or "")]
    needles.extend(meta.get("cues") or [])
    return any(needle and needle in normalized for needle in needles)


def _hits_from_cues(
    normalized: str,
    catalog: dict[str, dict],
    seen: set[str],
    max_topics: int,
) -> list[TopicHit]:
    """اگر مدل کدی در درخت نداد، از نشانه‌های داخل متن حوزه را برمی‌دارد."""
    scored: list[tuple[int, int, dict, str]] = []
    for meta in catalog.values():
        if meta["code"] in seen:
            continue
        cues = sorted((meta.get("cues") or []), key=len, reverse=True)
        for cue in cues:
            if cue and cue in normalized:
                scored.append((len(cue), int(meta["level"]), meta, cue))
                break
    scored.sort(reverse=True)
    hits: list[TopicHit] = []
    for _length, _level, meta, cue in scored:
        if meta["code"] in seen:
            continue
        hits.append(
            _hit_from_meta(
                meta,
                catalog,
                is_primary=False,
                mention=cue,
                confidence=0.6,
                normalized=normalized,
            )
        )
        seen.add(str(meta["code"]))
        if len(hits) >= max_topics:
            break
    return hits


def _normalize_discovered_code(raw: Any) -> str:
    """کد انگلیسی موضوع نو را یکدست می‌کند."""
    text = str(raw or "").strip().lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not _CODE_RE.fullmatch(text):
        return ""
    return text[:80]


def _code_from_label(label: str, catalog: dict[str, dict], seen: set[str]) -> str:
    """از نام فارسی هم کد پایدار می‌سازد؛ کد کاتالوگ را دوباره استفاده نمی‌کند."""
    latin = _normalize_discovered_code(label)
    if latin and latin not in catalog and latin not in seen:
        return latin
    digest = hashlib.sha1((label or "topic").encode("utf-8")).hexdigest()[:10]
    code = f"topic_{digest}"
    if code in catalog or code in seen:
        code = f"topic_{digest}x"
    return code


def _snippet_mention(normalized: str) -> str:
    """اگر شاهد دقیق نبود، تکهٔ کوتاهی از خود متن را شاهد می‌گیرد."""
    text = (normalized or "").strip()
    if not text:
        return ""
    if len(text) <= 80:
        return text
    cut = text[:80]
    space = cut.rfind(" ")
    return cut[:space] if space > 20 else cut


def _label_from_text(normalized: str) -> str:
    """برچسب کوتاه موضوع را از خود جمله می‌گیرد."""
    words = (normalized or "").split()
    return " ".join(words[:8])[:100]


def _mention_of(normalized: str, *candidates: str) -> str:
    """اول شاهد مدل، بعد همپوشانی با متن، وگرنه تکهٔ خود متن."""
    for raw in candidates:
        mention = clean_text(str(raw or ""))
        if not mention:
            continue
        span = find_span(normalized, mention)
        if span is not None:
            return normalized[span[0] : span[1]]
        words = mention.split()
        for length in range(len(words), 0, -1):
            piece = " ".join(words[:length])
            span = find_span(normalized, piece)
            if span is not None:
                return normalized[span[0] : span[1]]
    return _snippet_mention(normalized)


def _hit_discovered(
    *,
    code: str,
    name: str,
    definition: str,
    mention: str,
    is_primary: bool,
    confidence: Any,
) -> TopicHit:
    """موضوع فهمیده‌شدهٔ خارج از درخت را می‌سازد."""
    label = (name or mention)[:100]
    return TopicHit(
        code=code,
        name=label,
        level=1,
        parent_code=None,
        path=[label],
        path_codes=[code],
        is_primary=bool(is_primary),
        mention_text=mention,
        confidence=accept_confidence(confidence or 0.7),
        discovered=True,
        definition=(definition or label),
    )


def _novel_from_item(
    item: dict,
    normalized: str,
    catalog: dict[str, dict],
    seen: set[str],
) -> TopicHit | None:
    """موضوع خارج از درخت را از نام مدل یا خود متن نگه می‌دارد."""
    name = clean_text(
        str(item.get("name") or item.get("topic") or item.get("label") or "").strip()
    )
    definition = clean_text(
        str(item.get("definition") or item.get("description") or "").strip()
    )
    if not name:
        name = definition or _label_from_text(normalized)
    if not name:
        return None
    requested = _normalize_discovered_code(item.get("code") or item.get("topic_code") or "")
    if requested in catalog or requested in seen:
        requested = ""
    code = requested or _code_from_label(name, catalog, seen)
    if not code or code in seen or code in catalog:
        return None
    mention = _mention_of(
        normalized,
        str(item.get("mention_text") or ""),
        str(item.get("evidence") or ""),
        name,
    )
    if not mention:
        return None
    return _hit_discovered(
        code=code,
        name=name,
        definition=definition,
        mention=mention,
        is_primary=bool(item.get("is_primary")),
        confidence=item.get("confidence") or 0.7,
    )


def _novel_from_text(
    normalized: str,
    catalog: dict[str, dict],
    seen: set[str],
) -> TopicHit | None:
    """اگر مدل موضوع نداد، باز هم موضوع جمله را از خود متن برمی‌گرداند."""
    name = _label_from_text(normalized)
    mention = _snippet_mention(normalized)
    if not name or not mention:
        return None
    code = _code_from_label(name, catalog, seen)
    if not code or code in seen or code in catalog:
        return None
    return _hit_discovered(
        code=code,
        name=name,
        definition=name,
        mention=mention,
        is_primary=True,
        confidence=0.55,
    )


def persist_discovered_topics(
    hits: list[TopicHit],
    path: Path | None = None,
) -> None:
    """موضوع نو را در YAML کشف‌شده می‌نویسد؛ ردیف قبلی را حذف نمی‌کند."""
    discovery = load_topic_discovery()
    if not discovery.get("persist"):
        return
    novel = [item for item in hits if item.discovered]
    if not novel:
        return
    target = path or discovered_topic_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if target.is_file():
        loaded = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        rows = loaded.get("topics") if isinstance(loaded, dict) else None
        if isinstance(rows, list):
            existing = [row for row in rows if isinstance(row, dict) and row.get("code")]
    by_code = {str(row.get("code")): row for row in existing}
    changed = False
    for hit in novel:
        if hit.code in by_code:
            continue
        existing.append(
            {
                "code": hit.code,
                "name": hit.name,
                "level": 1,
                "discovered": True,
                "definition": hit.definition or hit.name,
                "description": hit.definition or hit.name,
                "cues": [hit.mention_text] if hit.mention_text else [],
                "aliases": [hit.name],
            }
        )
        by_code[hit.code] = existing[-1]
        changed = True
    if not changed:
        return
    header = (
        "# موضوع‌هایی که از متن کشف شده‌اند و در درخت اصلی نبوده‌اند.\n"
        "# با دست حذف نکنید و به گره‌های topics.yaml تقلیل ندهید.\n\n"
    )
    dumped = yaml.safe_dump(
        {"topics": existing},
        allow_unicode=True,
        sort_keys=False,
    )
    target.write_text(header + dumped, encoding="utf-8")


def topics_from_payload(payload: Any, normalized: str) -> list[TopicHit]:
    """موضوع کاتالوگ یا موضوع کشف‌شده از متن را برمی‌دارد."""
    if not isinstance(payload, dict):
        payload = {}
    raw_topics = payload.get("topics")
    if not isinstance(raw_topics, list):
        raw_topics = []
    catalog = {item["code"]: item for item in load_topic_catalog()}
    max_topics = int(
        ((load_column_config(_SOURCE_KEY).get("ranges") or {}).get("topics") or {}).get(
            "max"
        )
        or 8
    )
    discovery = load_topic_discovery()
    hits: list[TopicHit] = []
    seen: set[str] = set()
    leftovers: list[dict] = []
    for item in raw_topics:
        if not isinstance(item, dict):
            continue
        if item.get("discovered"):
            leftovers.append(item)
            continue
        raw_code = str(item.get("code") or item.get("topic_code") or "").strip()
        name_hint = str(item.get("name") or "").strip()
        code = resolve_topic_code(raw_code, catalog, name_hint)
        meta = catalog.get(code) if code else None
        if meta is None or code in seen:
            leftovers.append(item)
            continue
        if meta.get("fallback") and not _has_topic_evidence(meta, normalized):
            leftovers.append(item)
            continue
        mention = clean_text(str(item.get("mention_text") or item.get("evidence") or ""))
        hits.append(
            _hit_from_meta(
                meta,
                catalog,
                is_primary=bool(item.get("is_primary")),
                mention=mention,
                confidence=item.get("confidence") or 0,
                normalized=normalized,
            )
        )
        seen.add(code)
        if len(hits) >= max_topics:
            break
    if not hits:
        hits.extend(_hits_from_cues(normalized, catalog, seen, max_topics))
    if not hits and discovery.get("enabled"):
        for item in leftovers:
            if len(hits) >= max_topics:
                break
            novel = _novel_from_item(item, normalized, catalog, seen)
            if novel is None:
                continue
            hits.append(novel)
            seen.add(novel.code)
        if not hits:
            novel = _novel_from_text(normalized, catalog, seen)
            if novel is not None:
                hits.append(novel)
                seen.add(novel.code)
    if hits and not any(item.is_primary for item in hits):
        best = max(hits, key=lambda item: (item.level, item.confidence))
        best.is_primary = True
    elif sum(1 for item in hits if item.is_primary) > 1:
        ranked_hits = sorted(
            hits,
            key=lambda item: (item.is_primary, item.level, item.confidence),
            reverse=True,
        )
        for item in hits:
            item.is_primary = item is ranked_hits[0]
    hits.sort(key=lambda item: (not item.is_primary, -item.level, -item.confidence))
    return hits
