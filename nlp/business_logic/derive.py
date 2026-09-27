"""رد فکت بدون شاهد و راستی‌آزمایی حساب استنتاج."""

import re
from typing import Any

from business_logic.normalizer import find_span
from schemas.output import FactHit

_EPS = 0.051
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def parse_number(value: Any) -> float | None:
    """عدد را از مقدار مدل یا رشته می‌خواند."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    match = _NUMBER.search(text.replace(",", ""))
    if match is None:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def number_in_text(value: float, text: str) -> bool:
    """اگر نمایش عدد در متن آمده باشد True است."""
    if not text:
        return False
    if float(value).is_integer():
        token = str(int(value))
    else:
        token = str(value).rstrip("0").rstrip(".")
    return token in text


def document_explicitness(facts: list[FactHit]) -> tuple[str, str]:
    """صراحت کل متن را از فکت‌های باقی‌مانده می‌سازد."""
    if not facts:
        return "none", "بدون فکت"
    if any(item.grounding == "derived" for item in facts):
        return "derived", "مستنتج از شاهد"
    return "explicit", "صریح"


def _source_values(fact: FactHit, by_id: dict[str, FactHit]) -> list[float] | None:
    """اعداد منابع را می‌خواند؛ منبع ناقص یعنی استنتاج رد است."""
    values: list[float] = []
    for source_id in fact.source_ids:
        source = by_id.get(source_id)
        if source is None or source.value is None:
            return None
        values.append(source.value)
    return values


def _arithmetic_ok(fact: FactHit, sources: list[float]) -> bool:
    """حساب اعلام‌شده با منابع می‌خواند یا نه."""
    if fact.value is None:
        return False
    derivation = fact.derivation
    if derivation in ("subtract", "remainder"):
        if len(sources) < 2:
            return False
        expected = sources[0] - sum(sources[1:])
        return abs(expected - fact.value) <= _EPS
    if derivation == "add":
        if not sources:
            return False
        return abs(sum(sources) - fact.value) <= _EPS
    return False


def keep_fact(fact: FactHit, by_id: dict[str, FactHit], normalized: str) -> bool:
    """فکت را فقط با شاهد متن یا حساب درست نگه می‌دارد."""
    mention_in_text = bool(
        fact.mention_text and find_span(normalized, fact.mention_text) is not None
    )
    for evidence in fact.evidence_texts:
        if find_span(normalized, evidence) is None:
            return False
    if fact.kind == "quantity" and fact.value is None:
        return False
    if fact.grounding == "explicit":
        if not mention_in_text:
            return False
        if fact.kind == "quantity" and fact.value is not None:
            haystack = fact.mention_text or normalized
            if not number_in_text(fact.value, haystack) and not number_in_text(
                fact.value, normalized
            ):
                return False
        return True
    if fact.grounding != "derived":
        return False
    if not fact.evidence_texts and not mention_in_text:
        return False
    if fact.kind == "quantity":
        sources = _source_values(fact, by_id)
        if sources is None:
            return False
        return _arithmetic_ok(fact, sources)
    return True


def add_verified_remainder(facts: list[FactHit]) -> list[FactHit]:
    """اگر کل و جزء صریح باشند و باقی در متن نیامده، تفاضل را به‌عنوان derived می‌سازد."""
    if any(item.role == "remainder" for item in facts):
        return facts
    totals = [
        item
        for item in facts
        if item.kind == "quantity" and item.role == "total" and item.value is not None
    ]
    parts = [
        item
        for item in facts
        if item.kind == "quantity" and item.role == "part" and item.value is not None
    ]
    if len(totals) != 1 or not parts:
        return facts
    total = totals[0]
    if any(item.unit != total.unit for item in parts):
        return facts
    leftover = total.value - sum(item.value for item in parts)
    if leftover <= _EPS:
        return facts
    part_names = {item.name for item in parts}
    part_mentions = " ".join(item.mention_text for item in parts)
    leftover_causes = [
        item
        for item in facts
        if item.kind == "cause"
        and item.name not in part_names
        and item.name not in part_mentions
    ]
    name = leftover_causes[0].name if leftover_causes else "باقی‌مانده"
    mention = leftover_causes[0].mention_text if leftover_causes else total.mention_text
    evidence = [total.mention_text] + [item.mention_text for item in parts]
    evidence = [part for part in evidence if part]
    facts.append(
        FactHit(
            fact_id="remainder_auto",
            kind="quantity",
            kind_name="مقدار",
            name=name,
            value=leftover,
            unit=total.unit,
            unit_name=total.unit_name,
            role="remainder",
            effect="",
            previous="",
            current="",
            grounding="derived",
            grounding_name="مستنتج از شاهد",
            derivation="subtract",
            source_ids=[total.fact_id] + [item.fact_id for item in parts],
            mention_text=mention,
            start_offset=leftover_causes[0].start_offset if leftover_causes else total.start_offset,
            end_offset=leftover_causes[0].end_offset if leftover_causes else total.end_offset,
            evidence_texts=evidence,
            confidence=min(item.confidence for item in [total, *parts]),
        )
    )
    return facts


def filter_facts(facts: list[FactHit], normalized: str) -> tuple[list[FactHit], int]:
    """فکت‌های بی‌شاهد یا با حساب غلط را کنار می‌گذارد."""
    by_id = {item.fact_id: item for item in facts if item.fact_id}
    kept: list[FactHit] = []
    for item in facts:
        if keep_fact(item, by_id, normalized):
            kept.append(item)
    dropped = len(facts) - len(kept)
    kept = add_verified_remainder(kept)
    return kept, dropped
