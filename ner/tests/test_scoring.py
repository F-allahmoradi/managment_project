"""امتیاز نمونه طلایی بدون مدل زبانی."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from tests.sample import GOLD_MENTIONS
from tests.scoring import score_mentions


class ScoringTests(unittest.TestCase):
    def test_perfect_match(self) -> None:
        score = score_mentions(GOLD_MENTIONS, GOLD_MENTIONS)
        self.assertEqual(score["tp"], len(GOLD_MENTIONS))
        self.assertEqual(score["fp"], 0)
        self.assertEqual(score["fn"], 0)
        self.assertEqual(score["f1"], 1.0)

    def test_alias_name_still_matches(self) -> None:
        predicted = [
            {
                "type": "ORG",
                "canonical_name": "شرکت پارس‌سازه",
                "mention_text": "شرکت پارس‌سازه",
            }
        ]
        gold = [
            {
                "type": "ORG",
                "canonical_name": "پارس‌سازه",
                "mention_text": "شرکت پارس‌سازه",
            }
        ]
        score = score_mentions(gold, predicted)
        self.assertEqual(score["tp"], 1)


if __name__ == "__main__":
    unittest.main()
