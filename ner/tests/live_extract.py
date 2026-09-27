"""اجرای زنده استخراج روی نمونه طلایی؛ چیزی در دیتابیس نوشته نمی‌شود."""

from pathlib import Path
import json
import sys

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.extractor import extract_entities
from tests.sample import GOLD_MENTIONS, SAMPLE_TEXT
from tests.scoring import score_mentions


def main() -> None:
    result = extract_entities(SAMPLE_TEXT)
    predicted = [item.model_dump() for item in result.mentions]
    score = score_mentions(GOLD_MENTIONS, predicted)
    payload = {
        "model_message": result.message,
        "text_length": result.text_length,
        "type_counts": result.type_counts,
        "canonical_entities": [item.model_dump() for item in result.entities],
        "mentions": predicted,
        "score": {
            "gold_count": score["gold_count"],
            "predicted_count": score["predicted_count"],
            "tp": score["tp"],
            "fp": score["fp"],
            "fn": score["fn"],
            "precision": score["precision"],
            "recall": score["recall"],
            "f1": score["f1"],
            "by_type": score["by_type"],
            "false_positive": score["false_positive"],
            "false_negative": score["false_negative"],
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
