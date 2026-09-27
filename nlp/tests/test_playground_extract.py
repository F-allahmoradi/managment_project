"""شکست یک لایه استخراج نباید فکت را دور بریزد؛ مدل جعلی بدون LLM."""

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch
import copy
import json
import sys
import unittest
import urllib.error
import urllib.request

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import LlmError
from playground import app as playground_app
from schemas.output import (
    ExtractFactsOutput,
    ExtractFrameOutput,
    ExtractQuotesOutput,
    FactHit,
    IssueFrameHit,
)
from tests.sample import GOLD_FACTS, GOLD_FRAME, GOLD_QUOTES, SAMPLE_TEXT


def _facts(text: str) -> ExtractFactsOutput:
    fact = FactHit(
        fact_id="q1",
        kind="quantity",
        kind_name="مقدار",
        name="کاهش عملکرد",
        value=30,
        unit="percent",
        unit_name="درصد",
        role="total",
        grounding="explicit",
        grounding_name="صریح",
        mention_text="30 درصد کاهش عملکرد",
        start_offset=0,
        end_offset=20,
        confidence=0.9,
    )
    return ExtractFactsOutput(
        status="success",
        message="1 فکت استخراج شد",
        source="project_texts",
        text_length=len(text),
        explicitness="explicit",
        explicitness_name="صریح",
        facts=[fact],
        fact_count=1,
    )


def _quotes(text: str) -> ExtractQuotesOutput:
    return ExtractQuotesOutput(
        status="success",
        message="نقل‌قولی استخراج نشد",
        source="project_texts",
        text_length=len(text),
    )


def _frame(text: str) -> ExtractFrameOutput:
    return ExtractFrameOutput(
        status="success",
        message="قاب مسئله استخراج شد",
        source="project_texts",
        text_length=len(text),
        frame=IssueFrameHit(
            title="کاهش عملکرد واحد مالی",
            unit="واحد مالی",
            process="staffing",
            process_name="تأمین نیرو",
            scope="organizational",
            scope_name="سازمانی",
            about="کمبود نیروی متخصص",
            mention_text="کمبود نیروی متخصص",
            confidence=0.8,
        ),
    )


def _boom(text: str):
    raise LlmError("زمان پاسخ مدل زبانی تمام شد")


class DumpAllIsolationTests(unittest.TestCase):
    """timeout نقل‌قول نباید فکت را پاک کند."""

    def test_keeps_facts_when_quotes_time_out(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "facts": _facts,
            "quotes": _boom,
            "frame": _frame,
        }
        try:
            payload = playground_app._dump_all("سارا آمد")
        finally:
            playground_app._LAYERS = original
        self.assertEqual(payload["fact_count"], 1)
        self.assertEqual(payload["facts"][0]["name"], "کاهش عملکرد")
        self.assertEqual(payload["quote_count"], 0)
        self.assertIsNotNone(payload["frame"])
        self.assertIn("نقل‌قول نیامد", payload["message"])
        self.assertIn("quotes", payload["layer_errors"])

    def test_all_layers_failing_raises(self) -> None:
        original = playground_app._LAYERS
        playground_app._LAYERS = {
            "facts": _boom,
            "quotes": _boom,
            "frame": _boom,
        }
        try:
            with self.assertRaises(LlmError):
                playground_app._dump_all("سارا آمد")
        finally:
            playground_app._LAYERS = original


def _fake_complete(system: str, user: str) -> dict:
    """پاسخ طلایی را بر اساس پرامپت لایه برمی‌گرداند؛ LLM نمی‌زند."""
    del user
    if "grounded facts" in system:
        return copy.deepcopy(GOLD_FACTS)
    if "quoted or reported speech" in system:
        return copy.deepcopy(GOLD_QUOTES)
    if "issue frame" in system:
        return copy.deepcopy(GOLD_FRAME)
    raise AssertionError("پرامپت لایه ناشناخته است")


def _assert_sample_extract(test: unittest.TestCase, payload: dict) -> None:
    """۳۰٪، ۱۰٪، باقی‌مانده ۲۰٪، دو علت، نقل‌قول و قاب باید در خروجی باشند."""
    test.assertEqual(payload.get("status"), "success")
    facts = payload.get("facts") or []
    quantities = {
        (item["role"], item["value"])
        for item in facts
        if item.get("kind") == "quantity"
    }
    test.assertIn(("total", 30.0), quantities)
    test.assertIn(("part", 10.0), quantities)
    test.assertIn(("remainder", 20.0), quantities)
    remainder = next(item for item in facts if item.get("role") == "remainder")
    test.assertEqual(remainder["grounding"], "derived")
    causes = {item["name"] for item in facts if item.get("kind") == "cause"}
    test.assertEqual(causes, {"کمبود نیروی متخصص", "واحد بازاریابی"})
    normalized = payload.get("normalized_text") or ""
    test.assertIn("30 درصد", normalized)
    test.assertIn("10 درصد", normalized)
    for item in facts:
        if item.get("kind") != "quantity" or item.get("role") == "remainder":
            continue
        start, end = item["start_offset"], item["end_offset"]
        test.assertGreaterEqual(start, 0)
        test.assertEqual(normalized[start:end], item["mention_text"])
    quotes = payload.get("quotes") or []
    test.assertEqual(len(quotes), 1)
    test.assertEqual(quotes[0]["attributed_to"], "واحد مالی")
    frame = payload.get("frame") or {}
    test.assertEqual(frame.get("unit"), "واحد مالی")
    test.assertEqual(frame.get("process"), "staffing")
    suggested = payload.get("suggested_task") or {}
    test.assertEqual(suggested.get("title"), "تأمین نیروی متخصص واحد مالی")
    test.assertEqual(suggested.get("source"), "frame")
    scoring = payload.get("suggested_scoring") or {}
    test.assertEqual(scoring.get("importance"), "زیاد")
    test.assertEqual(scoring.get("urgency"), "کم")
    test.assertEqual(scoring.get("severity"), "متوسط")
    test.assertEqual(
        [item["impact_type"] for item in scoring.get("impacts") or []],
        ["منابع انسانی", "کیفیت"],
    )


class FakeModelPlaygroundTests(unittest.TestCase):
    """زمین بازی با مدل جعلی همان متن نمونه را بدون کلید API استخراج می‌کند."""

    def test_dump_all_sample_has_percents_causes_quote_and_frame(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=_fake_complete,
        ):
            payload = playground_app._dump_all(SAMPLE_TEXT)
        _assert_sample_extract(self, payload)
        self.assertEqual(payload["layer"], "all")
        self.assertNotIn("writes_postgres", payload)

    def test_dump_facts_layer_keeps_witness_offsets(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=_fake_complete,
        ):
            payload = playground_app._dump_layer("facts", SAMPLE_TEXT)
        self.assertEqual(payload["layer"], "facts")
        self.assertEqual(payload["tool"], "extract_facts")
        quantities = {
            (item["role"], item["value"])
            for item in payload["facts"]
            if item["kind"] == "quantity"
        }
        self.assertIn(("remainder", 20.0), quantities)


class PlaygroundHttpTests(unittest.TestCase):
    """صفحه و API localhost کار می‌کنند؛ ذخیره جدا از استخراج است."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            playground_app.PlaygroundHandler,
        )
        cls.thread = Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.httpd.server_address
        cls.base = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def _post(self, path: str, body: dict) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": raw}
            return exc.code, payload

    def test_home_has_layer_buttons_and_save(self) -> None:
        with urllib.request.urlopen(f"{self.base}/") as response:
            html = response.read().decode("utf-8")
        self.assertIn("نمونه ساختگی", html)
        self.assertIn('data-layer="facts"', html)
        self.assertIn('data-layer="quotes"', html)
        self.assertIn('data-layer="frame"', html)
        self.assertIn('data-layer="all"', html)
        self.assertIn('id="btn-save"', html)
        self.assertIn("ذخیره پیشنهادی", html)
        js = (_ROOT / "playground" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("facts: (lastExtract.payload.facts || []).map", js)
        self.assertIn("fact_id: item.fact_id || item.id", js)
        self.assertIn("quotes: (lastExtract.payload.quotes || []).map", js)
        self.assertIn("attributed_to: item.attributed_to", js)
        self.assertIn('data-pane="causes"', html)
        self.assertIn("علت‌ها", html)
        self.assertIn('data-pane="task"', html)
        self.assertIn("وظیفه", html)
        self.assertIn('data-pane="score"', html)
        self.assertIn("امتیاز", html)
        self.assertIn('data-pane="ner"', html)
        self.assertIn("موضوع و موجودیت", html)

    def test_sample_returns_finance_text(self) -> None:
        with urllib.request.urlopen(f"{self.base}/api/sample") as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["text"], SAMPLE_TEXT)
        self.assertIn("واحد مالی", payload["text"])
        self.assertIn("۳۰ درصد", payload["text"])

    def test_extract_sample_with_fake_model(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=_fake_complete,
        ):
            status, payload = self._post("/api/extract", {"text": SAMPLE_TEXT})
        self.assertEqual(status, 200)
        _assert_sample_extract(self, payload)

    def test_blank_text_is_rejected(self) -> None:
        status, payload = self._post("/api/extract/facts", {"text": "  "})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error_code"], "INVALID_INPUT")

    def test_save_without_frame_is_invalid(self) -> None:
        status, payload = self._post("/api/save", {"text": SAMPLE_TEXT})
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("status"), "error")
        self.assertEqual(payload.get("error_code"), "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
