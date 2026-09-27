"""تست تبدیل تاریخ شمسی ذکر TIME به occurred_at."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.time_parse import jalali_to_gregorian, parse_occurred_at


class TimeParseTests(unittest.TestCase):
    """شاهد فارسی باید تاریخ میلادی پایدار بدهد."""

    def test_shahrivar_17_1404(self) -> None:
        self.assertEqual(jalali_to_gregorian(1404, 6, 17), (2025, 9, 8))
        self.assertEqual(parse_occurred_at("۱۷ شهریور ۱۴۰۴"), "2025-09-08 00:00:00")

    def test_weekday_and_hour(self) -> None:
        self.assertEqual(
            parse_occurred_at("چهارشنبه ۲۵ شهریور ۱۴۰۴ ساعت ۱۶"),
            "2025-09-16 16:00:00",
        )

    def test_iso_passthrough(self) -> None:
        self.assertEqual(
            parse_occurred_at("2025-09-08T00:00:00"),
            "2025-09-08 00:00:00",
        )

    def test_empty_is_none(self) -> None:
        self.assertIsNone(parse_occurred_at(None, "", "فردا"))


if __name__ == "__main__":
    unittest.main()
