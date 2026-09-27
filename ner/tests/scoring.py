"""امتیازدهی استخراج در برابر نمونه طلایی؛ بدون INSERT."""

from business_logic.normalizer import normalize_name


def _aliases(item: dict) -> set[str]:
    names = {
        normalize_name(item.get("canonical_name") or ""),
        normalize_name(item.get("mention_text") or ""),
    }
    return {name for name in names if name}


def _same_entity(gold: dict, predicted: dict) -> bool:
    if gold["type"] != predicted["type"]:
        return False
    gold_names = _aliases(gold)
    pred_names = _aliases(predicted)
    for left in gold_names:
        for right in pred_names:
            if left == right or left in right or right in left:
                return True
    return False


def _match(gold: list[dict], predicted: list[dict]) -> tuple[list, list, list]:
    remaining_pred = list(enumerate(predicted))
    true_positive = []
    false_negative = []
    for gold_item in gold:
        match_index = None
        for index, pred_item in remaining_pred:
            if _same_entity(gold_item, pred_item):
                match_index = index
                true_positive.append({"gold": gold_item, "predicted": pred_item})
                break
        if match_index is None:
            false_negative.append(gold_item)
        else:
            remaining_pred = [
                item for item in remaining_pred if item[0] != match_index
            ]
    false_positive = [item for _, item in remaining_pred]
    return true_positive, false_positive, false_negative


def _rates(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return round(precision, 3), round(recall, 3), round(f1, 3)


def score_mentions(gold: list[dict], predicted: list[dict]) -> dict:
    """precision / recall / F1 را روی ذکرها حساب می‌کند."""
    true_positive, false_positive, false_negative = _match(gold, predicted)
    tp = len(true_positive)
    fp = len(false_positive)
    fn = len(false_negative)
    precision, recall, f1 = _rates(tp, fp, fn)
    types = sorted({item["type"] for item in gold} | {item["type"] for item in predicted})
    by_type: dict[str, dict] = {}
    for entity_type in types:
        type_gold = [item for item in gold if item["type"] == entity_type]
        type_pred = [item for item in predicted if item["type"] == entity_type]
        type_tp, type_fp, type_fn = _match(type_gold, type_pred)
        p, r, f = _rates(len(type_tp), len(type_fp), len(type_fn))
        by_type[entity_type] = {
            "gold": len(type_gold),
            "predicted": len(type_pred),
            "tp": len(type_tp),
            "precision": p,
            "recall": r,
            "f1": f,
        }
    return {
        "gold_count": len(gold),
        "predicted_count": len(predicted),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "by_type": by_type,
    }
