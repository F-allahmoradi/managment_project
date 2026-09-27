"""عنوان پیشنهادی وظیفه از نیت یا قاب مسئله."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.suggest import suggest_task_title
from schemas.output import IssueFrameHit
from tests.sample import GOLD_FRAME


class SuggestTaskTests(unittest.TestCase):
    """نمونه کاهش عملکرد باید تأمین نیروی متخصص واحد مالی بدهد."""

    def test_sample_frame_suggests_staffing_task(self) -> None:
        frame = IssueFrameHit(
            title="کاهش عملکرد واحد مالی",
            unit="واحد مالی",
            process="staffing",
            process_name="تأمین نیرو",
            scope="organizational",
            scope_name="سازمانی",
            about="کمبود نیروی متخصص",
            mention_text="کمبود نیروی متخصص",
            confidence=0.8,
        )
        suggested = suggest_task_title(frame=frame)
        self.assertIsNotNone(suggested)
        self.assertEqual(suggested["title"], "تأمین نیروی متخصص واحد مالی")
        self.assertEqual(suggested["source"], "frame")

    def test_gold_frame_dict_matches_sample(self) -> None:
        suggested = suggest_task_title(frame=GOLD_FRAME["frame"])
        self.assertEqual(suggested["title"], "تأمین نیروی متخصص واحد مالی")

    def test_intent_action_wins_over_frame(self) -> None:
        suggested = suggest_task_title(
            intents=[
                {
                    "code": "request_action",
                    "is_primary": True,
                    "slots": {"عمل مطلوب": "جذب حسابدار ارشد"},
                }
            ],
            frame=GOLD_FRAME["frame"],
        )
        self.assertEqual(suggested["title"], "جذب حسابدار ارشد")
        self.assertEqual(suggested["source"], "intent")

    def test_without_frame_or_intent_is_none(self) -> None:
        self.assertIsNone(suggest_task_title(frame={"title": "کاهش عملکرد"}))


if __name__ == "__main__":
    unittest.main()
