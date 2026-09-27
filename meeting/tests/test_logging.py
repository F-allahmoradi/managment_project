"""تست ماژول لاگ‌گیری جلسات: کنسول، فایل، مراحل، و مدت عملیات.

به دیتابیس وصل نمی‌شود.
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
        settings = load_logging_config()
        self.assertTrue(settings["console"])
        self.assertTrue(settings["file"]["enabled"])
        self.assertTrue(settings["include_trace_in_response"])

    def test_tool_writes_file_and_not_stdout(self) -> None:
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
        self.assertEqual(payload["status"], "success")

    def test_trace_lists_steps_and_duration(self) -> None:
        payload = _demo_tool()
        trace = payload["trace"]
        self.assertEqual(trace["name"], "demo_tool")
        self.assertEqual(trace["status"], "success")
        step_names = [step["name"] for step in trace["steps"]]
        self.assertIn("fetch", step_names)

    def test_error_payload_marks_trace_error(self) -> None:
        payload = _broken_tool()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["trace"]["status"], "error")

    def test_step_without_parent_is_silent(self) -> None:
        self._lines.clear()
        values = _fake_fetch()
        self.assertEqual(values, [1, 2, 3])
        self.assertEqual(self._lines, [])

    def test_failed_step_is_logged_then_reraised(self) -> None:
        @logged_step("calculate")
        def boom() -> None:
            raise RuntimeError("fail")

        with self.assertRaises(RuntimeError):
            with log_operation("failing_tool"):
                boom()
        joined = "\n".join(self._lines)
        self.assertIn("step=calculate", joined)
        self.assertIn("status=error", joined)


if __name__ == "__main__":
    unittest.main()
