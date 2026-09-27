"""شکست یک لایه استخراج نباید نتیجهٔ موجودیت را دور بریزد."""

from pathlib import Path
import sys
import threading
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import LlmError
from playground import app as playground_app
from schemas.output import (
    EntityMentionHit,
    ExtractDiscourseOutput,
    ExtractEntitiesOutput,
    ExtractIntentOutput,
    ExtractKeywordsOutput,
    ExtractRhetoricOutput,
    RhetoricHit,
)


def _entities(text: str) -> ExtractEntitiesOutput:
    mention = EntityMentionHit(
        type="PERSON",
        canonical_name="سارا",
        normalized_name="سارا",
        mention_text="سارا",
        start_offset=0,
        end_offset=4,
        confidence=0.9,
    )
    return ExtractEntitiesOutput(
        status="success",
        message="1 ذکر موجودیت استخراج شد",
        source="project_texts",
        table="entity_mentions",
        column="mention_text",
        text_length=len(text),
        extracted_count=1,
        canonical_count=1,
        mentions=[mention],
    )


def _keywords(text: str) -> ExtractKeywordsOutput:
    return ExtractKeywordsOutput(
        status="success",
        message="کلمهٔ کلیدی استخراج نشد",
        source="project_texts",
        text_length=len(text),
    )


def _boom(text: str):
    raise LlmError("زمان پاسخ مدل زبانی تمام شد")


def _empty_speech(name: str, text: str):
    length = len(text)
    if name == "discourse":
        return ExtractDiscourseOutput(
            status="success",
            message="ژانری استخراج نشد",
            source="project_texts",
            text_length=length,
        )
    return ExtractIntentOutput(
        status="success",
        message="نیتی استخراج نشد",
        source="project_texts",
        text_length=length,
    )


def _empty_rhetoric(text: str) -> ExtractRhetoricOutput:
    return ExtractRhetoricOutput(
        status="success",
        message="بیانی استخراج نشد",
        source="project_texts",
        text_length=len(text),
    )


class DumpAllIsolationTests(unittest.TestCase):
    """timeout موضوع نباید موجودیت را پاک کند."""

    def test_keeps_entities_when_topics_time_out(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "entities": _entities,
            "keywords": _keywords,
            "topics": _boom,
            "sentiment": _boom,
            "discourse": lambda text: _empty_speech("discourse", text),
            "intent": lambda text: _empty_speech("intent", text),
            "rhetoric": _empty_rhetoric,
        }
        try:
            payload = playground_app._dump_all("سارا آمد")
        finally:
            playground_app._LAYERS = original
        self.assertEqual(payload["extracted_count"], 1)
        self.assertEqual(payload["mentions"][0]["canonical_name"], "سارا")
        self.assertEqual(payload["topic_count"], 0)
        self.assertIn("موضوع نیامد", payload["message"])
        self.assertIn("topics", payload["layer_errors"])

    def test_all_layers_failing_raises(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "entities": _boom,
            "keywords": _boom,
            "topics": _boom,
            "sentiment": _boom,
            "discourse": _boom,
            "intent": _boom,
            "rhetoric": _boom,
        }
        try:
            with self.assertRaises(LlmError):
                playground_app._dump_all("سارا آمد")
        finally:
            playground_app._LAYERS = original


class MeaningDependencyTests(unittest.TestCase):
    """احساس و ژانر و نیت تا برگشتن بیان صبر می‌کنند و معنا را می‌گیرند."""

    def test_irony_meaning_is_passed_after_rhetoric(self) -> None:
        entities_started = threading.Event()
        overlapped: list[bool] = []
        received: dict[str, str | None] = {}
        meaning = "سرور قطع شده و گوینده معترض است"

        def rhetoric(text: str) -> ExtractRhetoricOutput:
            overlapped.append(entities_started.wait(2))
            return ExtractRhetoricOutput(
                status="success",
                message="بیان کنایه استخراج شد",
                source="project_texts",
                text_length=len(text),
                rhetorics=[
                    RhetoricHit(
                        code="irony",
                        name="کنایه",
                        is_primary=True,
                        mention_text="چه عالی",
                        confidence=0.9,
                    )
                ],
                rhetoric_count=1,
                intended_meaning=meaning,
            )

        def entities(text: str) -> ExtractEntitiesOutput:
            entities_started.set()
            return _entities(text)

        def remember(name: str):
            def run(text: str, intended_meaning: str | None = None):
                received[name] = intended_meaning
                return _empty_speech(name, text) if name != "sentiment" else playground_app._empty_layer(name, text)

            return run

        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "entities": entities,
            "keywords": _keywords,
            "topics": _boom,
            "sentiment": remember("sentiment"),
            "discourse": remember("discourse"),
            "intent": remember("intent"),
            "rhetoric": rhetoric,
        }
        try:
            payload = playground_app._dump_all("چه عالی، باز هم سرور قطع شد")
        finally:
            playground_app._LAYERS = original
        self.assertEqual(overlapped, [True])
        self.assertEqual(payload["intended_meaning"], meaning)
        self.assertEqual(received["sentiment"], meaning)
        self.assertEqual(received["discourse"], meaning)
        self.assertEqual(received["intent"], meaning)
        self.assertIn("topics", payload["layer_errors"])
        self.assertEqual(payload["extracted_count"], 1)

    def test_literal_rhetoric_does_not_rewrite_later_layers(self) -> None:
        received: dict[str, str | None] = {}

        def rhetoric(text: str) -> ExtractRhetoricOutput:
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
                    )
                ],
                rhetoric_count=1,
                intended_meaning="سرور قطع است",
            )

        def remember(name: str):
            def run(text: str, intended_meaning: str | None = None):
                received[name] = intended_meaning
                if name == "sentiment":
                    return playground_app._empty_layer(name, text)
                return _empty_speech(name, text)

            return run

        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "entities": _entities,
            "keywords": _keywords,
            "topics": _keywords,
            "sentiment": remember("sentiment"),
            "discourse": remember("discourse"),
            "intent": remember("intent"),
            "rhetoric": rhetoric,
        }
        try:
            playground_app._collect_layers("سرور قطع است")
        finally:
            playground_app._LAYERS = original
        self.assertIsNone(received["sentiment"])
        self.assertIsNone(received["discourse"])
        self.assertIsNone(received["intent"])


if __name__ == "__main__":
    unittest.main()
