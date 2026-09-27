"""تست سرویس جلسه: الگو، تولید هفتهٔ بعد، تداخل، XOR شرکت‌کننده."""

from pathlib import Path
from datetime import datetime, time
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.generator import generate_meetings
from business_logic.meetings import (
    cancel_meeting,
    fetch_meeting,
    insert_meeting,
)
from business_logic.participants import insert_participant
from business_logic.record import record_meeting
from business_logic.repository import fetch_participant_records, fetch_sync_item_records
from business_logic.schedules import fetch_schedule, insert_schedule
from business_logic.sync import sync_meeting
from errors.crud import (
    INVALID_INPUT,
    MEETING_SLOT_CONFLICT,
    InvalidInputError,
    MeetingSlotConflictError,
)
from pydantic import ValidationError
from services.content import insert_content
from services.external_contact import insert_external_contact
from services.project import insert_project
from services.project_member import insert_project_member
from services.task import fetch_task
from validators.participant import validate_create_meeting_participant
from tests.conftest import (
    delete_temp_external_contact,
    delete_temp_meeting,
    delete_temp_project,
    delete_temp_schedule,
    delete_temp_user,
    insert_temp_user,
    unique_contact_name,
    unique_meeting_title,
    unique_phone,
    unique_project_name,
)

_NOW = datetime(2026, 9, 15, 12, 0)
_NEXT_WEDNESDAY = "2026-09-23T10:00:00"
_WEEK_AFTER = "2026-09-30T10:00:00"


class MeetingServiceTests(unittest.TestCase):
    """الگوی چهارشنبه ۱۰:۰۰، تولید هفتهٔ بعد، و رد XOR روی Postgres."""

    def test_schedule_generate_conflict_and_xor_participants(self) -> None:
        manager_id = insert_temp_user(last_name="مدیر-جلسه")
        teammate_id = insert_temp_user(last_name="عضو-جلسه")
        contact_id = None
        schedule_id = None
        meeting_id = None
        second_id = None
        try:
            schedule_id = insert_schedule(
                {
                    "meeting_type": "جلسه تیم",
                    "day_name": "چهارشنبه",
                    "start_time": time(10, 0),
                    "duration_minutes": 60,
                },
                user_id=manager_id,
            )
            schedule = fetch_schedule(schedule_id)
            self.assertEqual(schedule["day_of_week"], 4)
            self.assertEqual(schedule["start_time"], "10:00:00")
            self.assertEqual(schedule["meeting_type_name"], "جلسه تیم")

            generated = generate_meetings(
                schedule_id,
                actor_id=manager_id,
                weeks_ahead=1,
                now=_NOW,
            )
            self.assertTrue(generated["created"])
            meeting_id = generated["id"]
            self.assertEqual(generated["scheduled_at"], _NEXT_WEDNESDAY)
            meeting = fetch_meeting(meeting_id)
            self.assertEqual(meeting["status_name"], "برنامه‌ریزی شده")
            self.assertEqual(meeting["visibility"], "PRIVATE")
            self.assertIsNone(meeting["content_id"])
            self.assertEqual(meeting["sync_status"], "NOT_SYNCED")
            self.assertEqual(meeting["schedule_id"], schedule_id)

            again = generate_meetings(
                schedule_id,
                actor_id=manager_id,
                weeks_ahead=1,
                now=_NOW,
            )
            self.assertFalse(again["created"])
            self.assertTrue(again["conflict"])
            self.assertEqual(again["suggested_at"], _WEEK_AFTER)
            self.assertEqual(again["conflicting_meeting_id"], meeting_id)

            with self.assertRaises(MeetingSlotConflictError) as raised:
                insert_meeting(
                    {
                        "title": unique_meeting_title("تداخل"),
                        "scheduled_at": datetime(2026, 9, 23, 10, 0),
                        "meeting_type": "مذاکره مدیران",
                        "duration_minutes": 60,
                    },
                    manager_user_id=manager_id,
                )
            self.assertEqual(raised.exception.error_code, MEETING_SLOT_CONFLICT)
            self.assertEqual(raised.exception.suggested_at, _WEEK_AFTER)

            contact_id = insert_external_contact(
                {
                    "name": unique_contact_name("وکیل"),
                    "phone": unique_phone(),
                },
                actor_id=manager_id,
            )
            insert_participant(
                {"meeting_id": meeting_id, "user_id": teammate_id},
                actor_id=manager_id,
            )
            insert_participant(
                {"meeting_id": meeting_id, "external_contact_id": contact_id},
                actor_id=manager_id,
            )
            people = fetch_participant_records(meeting_id)
            self.assertEqual(len(people), 2)
            targets = {
                (row["user_id"], row["external_contact_id"]) for row in people
            }
            self.assertEqual(
                targets,
                {(teammate_id, None), (None, contact_id)},
            )
            with self.assertRaises(ValidationError):
                validate_create_meeting_participant(
                    {
                        "meeting_id": meeting_id,
                        "user_id": teammate_id,
                        "external_contact_id": contact_id,
                    }
                )
            with self.assertRaises(InvalidInputError) as xor_error:
                insert_participant(
                    {
                        "meeting_id": meeting_id,
                        "user_id": teammate_id,
                        "external_contact_id": contact_id,
                    },
                    actor_id=manager_id,
                )
            self.assertEqual(xor_error.exception.error_code, INVALID_INPUT)

            cancel_meeting(meeting_id, actor_id=manager_id)
            cancelled = fetch_meeting(meeting_id)
            self.assertEqual(cancelled["status_name"], "لغو شده")
            second = generate_meetings(
                schedule_id,
                actor_id=manager_id,
                weeks_ahead=1,
                now=_NOW,
            )
            self.assertTrue(second["created"])
            second_id = second["id"]
            self.assertEqual(second["scheduled_at"], _NEXT_WEDNESDAY)
        finally:
            if second_id is not None:
                delete_temp_meeting(second_id)
            if meeting_id is not None:
                delete_temp_meeting(meeting_id)
            if schedule_id is not None:
                delete_temp_schedule(schedule_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            delete_temp_user(teammate_id)
            delete_temp_user(manager_id)


class MeetingRecordSyncServiceTests(unittest.TestCase):
    """ضبط متن و همگام گزارش/تصمیم/وظیفه، و رد جلسهٔ خصوصی."""

    def test_team_record_sync_and_private_rejected(self) -> None:
        manager_id = insert_temp_user(last_name="مدیر-ضبط")
        teammate_id = insert_temp_user(last_name="مسئول-ضبط")
        project_id = None
        team_id = None
        private_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس-همگام"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=manager_id,
            )
            insert_project_member(
                {
                    "project_id": project_id,
                    "user_id": teammate_id,
                    "project_role": "عضو",
                },
                actor_id=manager_id,
            )
            team_id = insert_meeting(
                {
                    "title": unique_meeting_title("تیم-سرویس"),
                    "scheduled_at": datetime(2028, 4, 11, 10, 0),
                    "meeting_type": "جلسه تیم",
                    "project_id": project_id,
                    "visibility": "PROJECT",
                },
                manager_user_id=manager_id,
            )
            content_id = insert_content(
                {
                    "content_kind": "TEXT",
                    "text_body": "متن ضبط جلسه تیم.",
                },
                created_by=manager_id,
            )
            record_meeting(team_id, content_id, actor_id=manager_id)
            meeting = fetch_meeting(team_id)
            self.assertEqual(meeting["status_name"], "ضبط شده")
            self.assertEqual(meeting["content_id"], content_id)

            result = sync_meeting(
                team_id,
                {
                    "confirm": False,
                    "decision_title": "تصمیم داشبورد",
                    "decision_description": "داشبورد اولویت است.",
                    "assigned_to_user_id": teammate_id,
                    "task_title": "بستن داشبورد",
                },
                actor_id=manager_id,
            )
            self.assertEqual(result["sync_status"], "SYNCED")
            self.assertEqual(
                fetch_task(result["task_id"])["assigned_to_user_id"],
                teammate_id,
            )
            synced = fetch_meeting(team_id)
            self.assertEqual(synced["status_name"], "همگام‌سازی شده")
            self.assertEqual(len(fetch_sync_item_records(team_id)), 1)

            private_id = insert_meeting(
                {
                    "title": unique_meeting_title("خصوصی-سرویس"),
                    "scheduled_at": datetime(2028, 4, 11, 16, 0),
                    "meeting_type": "مذاکره مدیران",
                    "visibility": "PRIVATE",
                },
                manager_user_id=manager_id,
            )
            private_content = insert_content(
                {"content_kind": "TEXT", "text_body": "بدون پروژه."},
                created_by=manager_id,
            )
            record_meeting(private_id, private_content, actor_id=manager_id)
            with self.assertRaises(InvalidInputError) as caught:
                sync_meeting(private_id, {"confirm": False}, actor_id=manager_id)
            self.assertEqual(caught.exception.error_code, INVALID_INPUT)
            private = fetch_meeting(private_id)
            self.assertEqual(private["sync_status"], "NOT_SYNCED")
        finally:
            if team_id is not None:
                delete_temp_meeting(team_id)
            if private_id is not None:
                delete_temp_meeting(private_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(teammate_id)
            delete_temp_user(manager_id)


if __name__ == "__main__":
    unittest.main()
