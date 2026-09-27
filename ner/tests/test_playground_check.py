"""سنجش ژانر و نیت در زمین‌بازی، بدون مدل زنده."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from playground import app as playground_app
from playground.speech_check import catalog_payload, score_speech_layer
from schemas.output import (
    DiscourseHit,
    ExtractDiscourseOutput,
    ExtractIntentOutput,
    ExtractRhetoricOutput,
    IntentHit,
    RhetoricHit,
)


def _rhetoric(text: str) -> ExtractRhetoricOutput:
    return ExtractRhetoricOutput(
        status="success",
        message="بیان صریح استخراج شد",
        source="project_texts",
        text_length=len(text),
        rhetorics=[
            RhetoricHit(
                code="literal",
                name="صریح",
                is_primary=True,
                mention_text="قطع است",
                confidence=0.7,
                slots={"محتوا": "قطع است"},
            )
        ],
        rhetoric_count=1,
        intended_meaning="سرور قطع است",
    )


def _discourse(text: str) -> ExtractDiscourseOutput:
    return ExtractDiscourseOutput(
        status="success",
        message="ژانر مسئله استخراج شد",
        source="project_texts",
        text_length=len(text),
        discourses=[
            DiscourseHit(
                code="issue",
                name="مسئله",
                is_primary=True,
                mention_text="قطع است",
                confidence=0.9,
                slots={"چیز درگیر": "سرور"},
            )
        ],
        discourse_count=1,
    )


def _intent(text: str) -> ExtractIntentOutput:
    return ExtractIntentOutput(
        status="success",
        message="نیت گزارش مشکل استخراج شد",
        source="project_texts",
        text_length=len(text),
        intents=[
            IntentHit(
                code="report_problem",
                name="گزارش مشکل",
                is_primary=True,
                mention_text="قطع است",
                confidence=0.88,
                slots={"مسئله": "قطع سرور"},
            )
        ],
        intent_count=1,
    )


class SpeechCheckTests(unittest.TestCase):
    """انتظار کاربر با کد اصلی لایه سنجیده می‌شود."""

    def test_catalogs_include_genre_and_intent(self) -> None:
        payload = catalog_payload()
        discourses = {item["code"] for item in payload["discourses"]}
        intents = {item["code"] for item in payload["intents"]}
        rhetorics = {item["code"] for item in payload["rhetorics"]}
        groups = {item["group"] for item in payload["samples"]}
        entity_types = {item["code"] for item in payload["entity_types"]}
        self.assertIn("issue", discourses)
        self.assertIn("complaint", intents)
        self.assertIn("irony", rhetorics)
        self.assertIn("PERSON", entity_types)
        self.assertEqual(
            groups, {"entity", "discourse", "intent", "rhetoric", "joint"}
        )
        self.assertTrue(payload["examples"])
        self.assertTrue(payload["joint_examples"])
        self.assertTrue(payload["topics"])
        self.assertTrue(payload["emotions"])
        self.assertIn("entities", {item["id"] for item in payload["layers"]})

    def test_empty_expected_is_observation(self) -> None:
        scored = score_speech_layer(
            {
                "status": "success",
                "discourses": [
                    {"code": "issue", "name": "مسئله", "is_primary": True}
                ],
                "tool": "extract_discourse",
                "trace": {"name": "extract_discourse", "duration_ms": 12.5},
            },
            "discourses",
            "",
        )
        self.assertIsNone(scored["ok"])
        self.assertEqual(scored["got"], "issue")
        self.assertEqual(scored["duration_ms"], 12.5)

    def test_check_scores_primary_codes_and_keeps_trace(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {
            **original,
            "discourse": _discourse,
            "intent": _intent,
            "rhetoric": _rhetoric,
        }
        try:
            result = playground_app._check_speech(
                {
                    "text": "سرور قطع است",
                    "expected_discourse": "issue",
                    "expected_intent": "complaint",
                }
            )
        finally:
            playground_app._LAYERS = original
        self.assertTrue(result["discourse"]["ok"])
        self.assertFalse(result["intent"]["ok"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["discourse"]["tool"], "extract_discourse")
        self.assertEqual(result["intent"]["tool"], "extract_intent")
        self.assertEqual(result["rhetoric"]["got"], "literal")
        self.assertEqual(result["intended_meaning"], "سرور قطع است")
        self.assertEqual(result["discourse"]["trace"]["name"], "extract_discourse")
        self.assertGreaterEqual(result["discourse"]["duration_ms"], 0)
        self.assertEqual(result["discourse"]["slots"]["چیز درگیر"], "سرور")

    def test_dump_layer_attaches_tool_trace(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {**original, "discourse": _discourse}
        try:
            payload = playground_app._dump_layer("discourse", "سرور قطع است")
        finally:
            playground_app._LAYERS = original
        self.assertEqual(payload["tool"], "extract_discourse")
        self.assertEqual(payload["discourses"][0]["code"], "issue")
        self.assertEqual(payload["trace"]["name"], "extract_discourse")
        self.assertIn("duration_ms", payload["trace"])


if __name__ == "__main__":
    unittest.main()
