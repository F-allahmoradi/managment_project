"""تست محاسبهٔ درصد و برچسب سلامت بدون دیتابیس."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.calculator import (
    HEALTH_AT_RISK,
    HEALTH_DELAYED,
    HEALTH_OK,
    health_label,
    is_at_risk,
    progress_percent,
)


class CalculatorTests(unittest.TestCase):
    def test_progress_is_completed_over_total(self) -> None:
        self.assertEqual(progress_percent(1, 2), 50.0)
        self.assertEqual(progress_percent(0, 0), 0.0)
        self.assertEqual(progress_percent(3, 3), 100.0)

    def test_health_uses_overdue_and_deadline(self) -> None:
        self.assertEqual(
            health_label(0, 5, "در حال اجرا", "تکمیل شده", "لغو شده"),
            HEALTH_OK,
        )
        self.assertEqual(
            health_label(1, 5, "در حال اجرا", "تکمیل شده", "لغو شده"),
            HEALTH_AT_RISK,
        )
        self.assertEqual(
            health_label(0, -1, "در حال اجرا", "تکمیل شده", "لغو شده"),
            HEALTH_DELAYED,
        )
        self.assertTrue(is_at_risk(HEALTH_AT_RISK))
        self.assertFalse(is_at_risk(HEALTH_OK))


if __name__ == "__main__":
    unittest.main()
