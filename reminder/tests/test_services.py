"""تست سرویس تعریف یادآوری: XOR گیرنده و نبود execution_logs."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from datetime import datetime

from business_logic.follow_up import (
    assert_one_target,
    execution_log_count,
    fetch_follow_up_states,
    fetch_reminder,
    fetch_reminders_for_actor,
    insert_reminder,
    prepare_target,
)
from errors.crud import INVALID_INPUT, InvalidInputError
from services.external_contact import insert_external_contact
from services.project import insert_project
from tests.conftest import (
    delete_temp_external_contact,
    delete_temp_project,
    delete_temp_reminder,
    delete_temp_user,
    insert_temp_user,
    unique_contact_name,
    unique_phone,
    unique_project_name,
    unique_reminder_title,
)


_WHEN = datetime(2026, 9, 16, 9, 0, 0)


class ReminderServiceTests(unittest.TestCase):
    """درج تعریف یادآوری روی Postgres بدون ارسال کانال."""

    def test_insert_creates_pending_follow_up_and_no_execution_log(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-یادآوری")
        member_id = insert_temp_user(last_name="گیرنده-یادآوری")
        stranger_id = insert_temp_user(last_name="غریبه-یادآوری")
        project_id = None
        contact_id = None
        reminder_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("سرویس-یادآوری"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=owner_id,
            )
            contact_id = insert_external_contact(
                {
                    "name": unique_contact_name("پیمانکار"),
                    "phone": unique_phone(),
                }
            )
            reminder_id = insert_reminder(
                {
                    "title": unique_reminder_title(),
                    "message_template": "گزارش هفتگی را بفرستید.",
                    "scheduled_at": _WHEN,
                    "reminder_type": "یک‌باره",
                    "frequency": "یک‌باره",
                    "project_id": project_id,
                    "target_user_id": member_id,
                    "target_external_contact_id": contact_id,
                },
                created_by=owner_id,
            )
            row = fetch_reminder(reminder_id)
            self.assertEqual(row["message_template"], "گزارش هفتگی را بفرستید.")
            self.assertEqual(row["status_name"], "فعال")
            self.assertNotIn("content_id", row)
            states = fetch_follow_up_states(reminder_id, limit=10, offset=0)
            self.assertEqual(len(states), 2)
            self.assertEqual({item["status_name"] for item in states}, {"در انتظار"})
            self.assertEqual({item["attempt_count"] for item in states}, {0})
            self.assertEqual(execution_log_count(reminder_id), 0)
            visible = fetch_reminders_for_actor(owner_id, limit=50, offset=0)
            self.assertIn(reminder_id, {item["id"] for item in visible})
            hidden = fetch_reminders_for_actor(stranger_id, limit=50, offset=0)
            self.assertNotIn(reminder_id, {item["id"] for item in hidden})
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(stranger_id)
            delete_temp_user(member_id)
            delete_temp_user(owner_id)

    def test_dual_target_on_one_row_and_missing_recipient_are_invalid(self) -> None:
        owner_id = insert_temp_user(last_name="xor-یادآوری")
        contact_id = insert_external_contact(
            {"name": unique_contact_name(), "phone": unique_phone()}
        )
        try:
            with self.assertRaises(InvalidInputError) as both:
                prepare_target(owner_id, contact_id)
            self.assertEqual(both.exception.error_code, INVALID_INPUT)
            with self.assertRaises(InvalidInputError) as neither:
                assert_one_target(None, None)
            self.assertEqual(neither.exception.error_code, INVALID_INPUT)
            with self.assertRaises(InvalidInputError) as missing:
                insert_reminder(
                    {
                        "title": unique_reminder_title(),
                        "message_template": "بدون گیرنده",
                        "scheduled_at": _WHEN,
                        "reminder_type": "یک‌باره",
                        "frequency": "یک‌باره",
                    },
                    created_by=owner_id,
                )
            self.assertEqual(missing.exception.error_code, INVALID_INPUT)
        finally:
            delete_temp_external_contact(contact_id)
            delete_temp_user(owner_id)


if __name__ == "__main__":
    unittest.main()
