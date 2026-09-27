"""تست فکت، نقل‌قول و قاب مسئله؛ مدل زبانی شبیه‌سازی می‌شود."""

from pathlib import Path
from unittest.mock import patch
import copy
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.extractor import extract_facts, extract_frame, extract_quotes
from business_logic.normalizer import normalize_text
from errors.crud import INVALID_INPUT, LLM_ERROR, LlmError
from mcp_server.tools.extract.extract_facts import run_extract_facts
from schemas.input import ExtractNlpInput
from tests.sample import GOLD_FACTS, GOLD_FRAME, GOLD_QUOTES, SAMPLE_TEXT


class ExtractorTests(unittest.TestCase):
    """خروجی مدل باید شاهد متن و حساب درست داشته باشد."""

    def test_gold_example_derives_remainder_percent(self) -> None:
        with patch("business_logic.extractor.complete_json", return_value=GOLD_FACTS):
            result = extract_facts(SAMPLE_TEXT)
        values = {
            (item.role, item.value)
            for item in result.facts
            if item.kind == "quantity"
        }
        self.assertIn(("total", 30.0), values)
        self.assertIn(("part", 10.0), values)
        self.assertIn(("remainder", 20.0), values)
        self.assertEqual(result.explicitness, "derived")
        self.assertEqual(result.dropped_count, 0)
        causes = {item.name for item in result.facts if item.kind == "cause"}
        self.assertEqual(causes, {"کمبود نیروی متخصص", "واحد بازاریابی"})

    def test_python_fills_remainder_if_model_omits_it(self) -> None:
        fake = {
            "facts": [
                item for item in GOLD_FACTS["facts"] if item["id"] != "q3"
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_facts(SAMPLE_TEXT)
        remainders = [item for item in result.facts if item.role == "remainder"]
        self.assertEqual(len(remainders), 1)
        self.assertEqual(remainders[0].value, 20.0)
        self.assertEqual(remainders[0].grounding, "derived")
        self.assertEqual(remainders[0].name, "کمبود نیروی متخصص")

    def test_wrong_remainder_is_replaced_by_verified_math(self) -> None:
        fake = copy.deepcopy(GOLD_FACTS)
        for item in fake["facts"]:
            if item["id"] == "q3":
                item["value"] = 25
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_facts(SAMPLE_TEXT)
        remainders = [item for item in result.facts if item.role == "remainder"]
        self.assertEqual(len(remainders), 1)
        self.assertEqual(remainders[0].value, 20.0)
        self.assertEqual(remainders[0].fact_id, "remainder_auto")
        self.assertGreaterEqual(result.dropped_count, 1)

    def test_guess_without_span_is_dropped(self) -> None:
        fake = {
            "facts": [
                {
                    "id": "x1",
                    "kind": "cause",
                    "name": "مدیرعامل مقصر است",
                    "grounding": "explicit",
                    "mention_text": "مدیرعامل مقصر است",
                    "confidence": 0.9,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_facts(SAMPLE_TEXT)
        self.assertEqual(result.fact_count, 0)
        self.assertEqual(result.explicitness, "none")

    def test_explicit_number_must_appear_in_text(self) -> None:
        fake = {
            "facts": [
                {
                    "id": "q1",
                    "kind": "quantity",
                    "name": "کاهش عملکرد",
                    "value": 40,
                    "unit": "percent",
                    "role": "total",
                    "grounding": "explicit",
                    "mention_text": "کاهش عملکرد",
                    "confidence": 0.9,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_facts(SAMPLE_TEXT)
        self.assertEqual(result.fact_count, 0)

    def test_quotes_keep_inner_speaker(self) -> None:
        with patch("business_logic.extractor.complete_json", return_value=GOLD_QUOTES):
            result = extract_quotes(SAMPLE_TEXT)
        self.assertEqual(result.quote_count, 1)
        quote = result.quotes[0]
        self.assertEqual(quote.mode, "indirect")
        self.assertEqual(quote.attributed_to, "واحد مالی")
        self.assertIn("کمبود نیروی متخصص", quote.quoted_text)

    def test_paraphrased_quote_is_dropped(self) -> None:
        fake = {
            "quotes": [
                {
                    "mode": "indirect",
                    "attributed_to": "واحد مالی",
                    "quoted_text": "عملکرد خیلی بد شده",
                    "mention_text": "گفت",
                    "confidence": 0.9,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_quotes(SAMPLE_TEXT)
        self.assertEqual(result.quote_count, 0)

    def test_frame_keeps_unit_from_text(self) -> None:
        with patch("business_logic.extractor.complete_json", return_value=GOLD_FRAME):
            result = extract_frame(SAMPLE_TEXT)
        self.assertIsNotNone(result.frame)
        self.assertEqual(result.frame.unit, "واحد مالی")
        self.assertEqual(result.frame.process, "staffing")
        self.assertEqual(result.frame.scope, "organizational")
        self.assertEqual(result.frame.about, "کمبود نیروی متخصص")

    def test_frame_drops_unit_not_in_text(self) -> None:
        fake = {
            "frame": {
                "title": "کاهش عملکرد",
                "unit": "واحد منابع انسانی",
                "process": "staffing",
                "scope": "organizational",
                "about": "کمبود نیروی متخصص",
                "confidence": 0.8,
            }
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_frame(SAMPLE_TEXT)
        self.assertEqual(result.frame.unit, "")

    def test_empty_text_is_invalid(self) -> None:
        with self.assertRaises(Exception):
            ExtractNlpInput(text="   ")

    def test_tool_rejects_blank_text(self) -> None:
        payload = run_extract_facts(text="  ")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)

    def test_tool_returns_facts(self) -> None:
        with patch("business_logic.extractor.complete_json", return_value=GOLD_FACTS):
            payload = run_extract_facts(text=SAMPLE_TEXT)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["explicitness"], "derived")
        self.assertNotIn("writes_postgres", payload)

    def test_llm_error_is_mapped(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=LlmError("اتصال به سرویس مدل زبانی برقرار نشد"),
        ):
            payload = run_extract_facts(text=SAMPLE_TEXT)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], LLM_ERROR)

    def test_normalize_converts_persian_digits(self) -> None:
        normalized = normalize_text(SAMPLE_TEXT)
        self.assertIn("30 درصد", normalized)
        self.assertIn("10 درصد", normalized)
        self.assertNotIn("۳۰", normalized)


if __name__ == "__main__":
    unittest.main()
