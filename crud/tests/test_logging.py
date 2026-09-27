"""تست ماژول لاگ‌گیری: کنسول، فایل، مراحل، و مدت عملیات.

به دیتابیس وصل نمی‌شود. ابزار ساختگی همان قرارداد MCP را تقلید می‌کند.
"""

from pathlib import Path
import io
import logging
import sys
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from logging_module import (
    log_operation,
    logged_step,
    logged_tool,
    reset_logging,
    setup_logging,
)
from logging_module.config import load_logging_config
from logging_module.setup import LOGGER_NAME
from middleware.request_logging import log_duration


@logged_step("fetch")
def _fake_fetch() -> list:
    return [1, 2, 3]


@logged_tool("demo_tool")
def _demo_tool() -> dict:
    values = _fake_fetch()
    return {"status": "success", "message": "ok", "n": len(values)}


@logged_tool("broken_tool")
def _broken_tool() -> dict:
    return {
        "status": "error",
        "error_code": "INVALID_INPUT",
        "message": "ورودی نامعتبر",
    }


class LoggingModuleTests(unittest.TestCase):
    """راه‌اندازی لاگر و ثبت مراحل و زمان را بررسی می‌کند."""

    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self._log_path = Path(self._tempdir.name) / "mcp.log"
        reset_logging()
        setup_logging(
            {
                "level": "INFO",
                "console": True,
                "include_trace_in_response": True,
                "file": {
                    "enabled": True,
                    "path": str(self._log_path),
                    "max_bytes": 1_000_000,
                    "backup_count": 1,
                },
            }
        )
        self._lines: list[str] = []
        handler = logging.Handler()
        handler.setFormatter(logging.Formatter("%(message)s"))

        def emit(record, captured=self._lines):
            captured.append(handler.format(record))

        handler.emit = emit
        logging.getLogger(LOGGER_NAME).addHandler(handler)
        self._list_handler = handler

    def tearDown(self) -> None:
        reset_logging()
        self._tempdir.cleanup()

    def test_yaml_config_has_console_and_file(self) -> None:
        """تنظیم پیش‌فرض باید هم کنسول و هم فایل را روشن کند."""
        settings = load_logging_config()
        self.assertTrue(settings["console"])
        self.assertTrue(settings["file"]["enabled"])
        self.assertTrue(settings["include_trace_in_response"])

    def test_tool_writes_file_and_not_stdout(self) -> None:
        """لاگ باید در فایل باشد و stdout را برای JSON-RPC خالی بگذارد."""
        stdout = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout
        try:
            payload = _demo_tool()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(stdout.getvalue(), "")
        text = self._log_path.read_text(encoding="utf-8")
        self.assertIn("event=start", text)
        self.assertIn("name=demo_tool", text)
        self.assertIn("event=step", text)
        self.assertIn("step=fetch", text)
        self.assertIn("event=end", text)
        self.assertIn("duration_ms=", text)
        self.assertEqual(payload["status"], "success")

    def test_trace_lists_steps_and_duration(self) -> None:
        """پاسخ ابزار باید مراحل و میلی‌ثانیه را نشان بدهد."""
        payload = _demo_tool()
        trace = payload["trace"]
        self.assertEqual(trace["name"], "demo_tool")
        self.assertEqual(trace["kind"], "tool")
        self.assertEqual(trace["status"], "success")
        self.assertIsInstance(trace["duration_ms"], float)
        self.assertGreaterEqual(trace["duration_ms"], 0)
        step_names = [step["name"] for step in trace["steps"]]
        self.assertIn("fetch", step_names)
        fetch = trace["steps"][0]
        self.assertEqual(fetch["detail"], "_fake_fetch")
        self.assertEqual(fetch["count"], 3)
        self.assertEqual(fetch["status"], "success")

    def test_error_payload_marks_trace_error(self) -> None:
        """اگر ابزار JSON خطا بدهد، لاگ و trace هم error باشند."""
        payload = _broken_tool()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["trace"]["status"], "error")
        self.assertEqual(payload["trace"]["error_code"], "INVALID_INPUT")
        joined = "\n".join(self._lines)
        self.assertIn("status=error", joined)

    def test_step_without_parent_is_silent(self) -> None:
        """توابع دامنه در تست مستقیم مرحله لاگ نکنند."""
        self._lines.clear()
        values = _fake_fetch()
        self.assertEqual(values, [1, 2, 3])
        self.assertEqual(self._lines, [])

    def test_legacy_log_duration_still_logs(self) -> None:
        """import قدیمی CRUD باید همان عملیات را لاگ کند."""
        with log_duration("legacy_tool"):
            pass
        joined = "\n".join(self._lines)
        self.assertIn("name=legacy_tool", joined)
        self.assertIn("event=end", joined)

    def test_failed_step_is_logged_then_reraised(self) -> None:
        """خطای مرحله باید duration داشته باشد و دوباره پرتاب شود."""

        @logged_step("calculate")
        def boom() -> None:
            raise RuntimeError("fail")

        with self.assertRaises(RuntimeError):
            with log_operation("failing_tool"):
                boom()
        joined = "\n".join(self._lines)
        self.assertIn("step=calculate", joined)
        self.assertIn("status=error", joined)

    def test_nested_steps_record_depth_and_chain(self) -> None:
        """مرحلهٔ تو در تو باید depth و path و chain داشته باشد."""

        @logged_step("inner")
        def inner() -> list:
            return [1, 2]

        @logged_step("outer")
        def outer() -> list:
            return inner()

        @logged_tool("nested_tool")
        def nested_tool() -> dict:
            values = outer()
            return {"status": "success", "n": len(values)}

        payload = nested_tool()
        trace = payload["trace"]
        self.assertEqual(trace["chain"], "inner,outer")
        self.assertEqual(trace["step_count"], 2)
        by_name = {step["name"]: step for step in trace["steps"]}
        self.assertEqual(by_name["inner"]["depth"], 1)
        self.assertEqual(by_name["inner"]["parent"], "outer")
        self.assertEqual(by_name["inner"]["path"], "outer/inner")
        self.assertEqual(by_name["outer"]["depth"], 0)
        self.assertEqual(by_name["outer"]["path"], "outer")
        joined = "\n".join(self._lines)
        self.assertIn("chain=inner,outer", joined)
        self.assertIn("path=outer/inner", joined)
        self.assertIn("slowest=", joined)

    def test_numeric_domain_result_is_not_logged(self) -> None:
        """عدد خام مرحله نباید در لاگ بیاید چون ممکن است دادهٔ حساس باشد."""

        @logged_step("calculate")
        def mean_like() -> int:
            return 42

        @logged_tool("secret_stat")
        def secret_stat() -> dict:
            mean_like()
            return {"status": "success"}

        payload = secret_stat()
        joined = "\n".join(self._lines)
        self.assertNotIn("result=42", joined)
        self.assertTrue(
            all(step.get("result") != 42 for step in payload["trace"]["steps"])
        )

    def test_insert_id_is_logged_as_id(self) -> None:
        """شناسهٔ ردیف بعد از insert با کلید id ثبت شود، نه result."""

        @logged_step("insert")
        def insert_like() -> int:
            return 19

        @logged_tool("create_like")
        def create_like() -> dict:
            insert_like()
            return {"status": "success", "id": 19}

        payload = create_like()
        step = payload["trace"]["steps"][0]
        self.assertEqual(step["id"], 19)
        joined = "\n".join(self._lines)
        self.assertIn("id=19", joined)
        self.assertNotIn("result=19", joined)

    def test_count_fields_from_dict_result(self) -> None:
        """شمار موجودیت و طول متن لاگ شود، نه مقدار نام."""

        @logged_step("extract")
        def extract() -> dict:
            return {"extracted_count": 3, "text_length": 10, "first_name": "علی"}

        @logged_tool("extract_tool")
        def extract_tool() -> dict:
            extract()
            return {"status": "success"}

        payload = extract_tool()
        step = payload["trace"]["steps"][0]
        self.assertEqual(step["extracted_count"], 3)
        self.assertEqual(step["text_length"], 10)
        joined = "\n".join(self._lines)
        self.assertNotIn("علی", joined)


if __name__ == "__main__":
    unittest.main()
