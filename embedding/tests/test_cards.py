"""ساخت کارت خام و فکت بدون مدل امبدینگ."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.cards import cards_for_analysis, entity_card, intent_card, raw_card


class CardTests(unittest.TestCase):
    """کارت فارسی باید شاهد داشته باشد نه JSON مدل."""

    def test_raw_and_facts_stay_separate(self) -> None:
        cards = cards_for_analysis(
            "message",
            "سارا تأخیر پرداخت پیمانکار را گزارش کرد.",
            {
                "entities": [
                    {
                        "id": 1,
                        "type": "PERSON",
                        "canonical_name": "سارا",
                        "normalized_name": "سارا",
                    }
                ],
                "mentions": [
                    {
                        "id": 11,
                        "entity_id": 1,
                        "mention_text": "سارا",
                    }
                ],
                "intents": [
                    {
                        "id": 2,
                        "code": "report_problem",
                        "name": "گزارش مشکل",
                        "mention_text": "تأخیر پرداخت پیمانکار را گزارش کرد",
                        "slots": {
                            "گزارش‌دهنده": "سارا",
                            "مسئله": "تأخیر پرداخت",
                        },
                    }
                ],
            },
        )
        kinds = [item["kind"] for item in cards]
        self.assertIn("raw", kinds)
        self.assertIn("entity", kinds)
        self.assertIn("intent", kinds)
        self.assertIn("intent_slot", kinds)
        raw = next(item for item in cards if item["kind"] == "raw")
        self.assertIn("پیام", raw["embedded_text"])
        self.assertIn("سارا", raw["embedded_text"])
        self.assertNotIn("report_problem", raw["embedded_text"])
        intent = next(item for item in cards if item["kind"] == "intent")
        self.assertIn("گزارش مشکل", intent["embedded_text"])
        self.assertIn("تأخیر پرداخت", intent["embedded_text"])
        self.assertIn("گزارش‌دهنده: سارا", intent["embedded_text"])
        self.assertEqual(2, sum(1 for item in cards if item["kind"] == "intent_slot"))

    def test_card_helpers_use_persian_labels(self) -> None:
        self.assertEqual(raw_card("message", "قطعه رسید")[:4], "پیام")
        self.assertIn("فرد", entity_card({"type": "PERSON", "canonical_name": "علی"}))
        self.assertIn("نیت: شکایت", intent_card({"name": "شکایت", "mention_text": "خسارت"}))


if __name__ == "__main__":
    unittest.main()
