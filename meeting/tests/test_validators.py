"""تست اعتبارسنجی XOR شرکت‌کننده و visibility بدون دیتابیس."""

from pathlib import Path
from datetime import datetime
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from pydantic import ValidationError
from schemas.meeting.meeting import (
    CreateMeetingInput,
    RecordMeetingInput,
    SyncMeetingInput,
    UpdateMeetingInput,
)
from schemas.meeting.participant import CreateMeetingParticipantInput
from schemas.meeting.schedule import CreateMeetingScheduleInput
from validators.participant import validate_create_meeting_participant
from business_logic.calendar import (
    occurrence_in_week,
    parse_day_of_week,
    week_start_saturday,
)


class MeetingValidatorTests(unittest.TestCase):
    """XOR و visibility و روز هفته را بدون Postgres می‌سنجد."""

    def test_participant_rejects_both_or_neither(self) -> None:
        with self.assertRaises(ValidationError):
            CreateMeetingParticipantInput(meeting_id=1, user_id=2, external_contact_id=3)
        with self.assertRaises(ValidationError):
            CreateMeetingParticipantInput(meeting_id=1)
        with self.assertRaises(ValidationError):
            validate_create_meeting_participant(
                {"meeting_id": 1, "user_id": 2, "external_contact_id": 3}
            )

    def test_participant_accepts_user_xor_external(self) -> None:
        user_row = CreateMeetingParticipantInput(meeting_id=1, user_id=2)
        self.assertEqual(user_row.user_id, 2)
        self.assertIsNone(user_row.external_contact_id)
        ext_row = CreateMeetingParticipantInput(meeting_id=1, external_contact_id=9)
        self.assertEqual(ext_row.external_contact_id, 9)
        self.assertIsNone(ext_row.user_id)

    def test_project_visibility_needs_project(self) -> None:
        with self.assertRaises(ValidationError):
            CreateMeetingInput(
                title="جلسه",
                scheduled_at=datetime(2026, 9, 23, 10, 0),
                meeting_type="جلسه تیم",
                visibility="PROJECT",
            )

    def test_update_meeting_requires_a_field(self) -> None:
        with self.assertRaises(ValidationError):
            UpdateMeetingInput(id=1)
        parsed = UpdateMeetingInput(id=1, title="عنوان تازه")
        self.assertEqual(parsed.title, "عنوان تازه")

    def test_schedule_requires_day(self) -> None:
        with self.assertRaises(ValidationError):
            CreateMeetingScheduleInput(
                meeting_type="جلسه تیم",
                start_time="10:00",
            )

    def test_wednesday_is_day_four(self) -> None:
        self.assertEqual(parse_day_of_week(day_name="چهارشنبه"), 4)
        self.assertEqual(parse_day_of_week(day_of_week=4), 4)

    def test_next_week_wednesday_from_tuesday(self) -> None:
        now = datetime(2026, 9, 15, 12, 0)
        self.assertEqual(week_start_saturday(now.date()).isoformat(), "2026-09-12")
        start, end = occurrence_in_week(4, "10:00", 60, 1, now)
        self.assertEqual(start.isoformat(), "2026-09-23T10:00:00")
        self.assertEqual(end.isoformat(), "2026-09-23T11:00:00")

    def test_record_and_sync_input_shapes(self) -> None:
        parsed = RecordMeetingInput(id=1, content_id=2)
        self.assertEqual(parsed.content_id, 2)
        with self.assertRaises(ValidationError):
            RecordMeetingInput(id=1)
        sync = SyncMeetingInput(id=3)
        self.assertFalse(sync.confirm)
        with_notes = SyncMeetingInput(
            id=3,
            confirm=True,
            notes="یادداشت دستی",
            decision_title="تصمیم",
        )
        self.assertEqual(with_notes.decision_title, "تصمیم")


if __name__ == "__main__":
    unittest.main()
