"""تست ارسال INTERNAL، execution_logs، و کلید idempotency."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from datetime import datetime

from business_logic.dispatcher import (
    default_idempotency_key,
    dispatch_reminder,
    fetch_execution_logs,
)
from business_logic.follow_up import (
    execution_log_count,
    fetch_follow_up_states,
    insert_reminder,
)
from errors.crud import INVALID_INPUT, InvalidInputError
from services.connection import open_connection
from services.external_contact import insert_external_contact
from tests.conftest import (
    delete_temp_external_contact,
    delete_temp_reminder,
    delete_temp_user,
    insert_temp_user,
    unique_contact_name,
    unique_phone,
    unique_reminder_title,
)


_WHEN = datetime(2026, 9, 16, 9, 0, 0)
_MESSAGE = "وضعیت پروژه را بفرستید."


class DispatcherServiceTests(unittest.TestCase):
    """ارسال INTERNAL روی Postgres واقعی بدون ابزار MCP."""

    def test_send_internal_user_and_replay_same_key(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-ارسال")
        member_id = insert_temp_user(last_name="گیرنده-ارسال")
        reminder_id = None
        try:
            title = unique_reminder_title()
            reminder_id = insert_reminder(
                {
                    "title": title,
                    "message_template": _MESSAGE,
                    "scheduled_at": _WHEN,
                    "reminder_type": "یک‌باره",
                    "frequency": "یک‌باره",
                    "target_user_id": member_id,
                },
                created_by=owner_id,
            )
            self.assertEqual(execution_log_count(reminder_id), 0)
            key = default_idempotency_key(
                reminder_id,
                member_id,
                None,
                "INTERNAL",
                1,
            )
            first = dispatch_reminder(
                {
                    "reminder_id": reminder_id,
                    "target_user_id": member_id,
                    "channel": "INTERNAL",
                    "idempotency_key": key,
                },
                actor_id=owner_id,
            )
            self.assertEqual(len(first), 1)
            self.assertFalse(first[0]["replayed"])
            self.assertEqual(first[0]["status"], "SENT")
            self.assertEqual(first[0]["idempotency_key"], key)
            self.assertIsNotNone(first[0]["notification_id"])
            states = fetch_follow_up_states(reminder_id, limit=10, offset=0)
            self.assertEqual(states[0]["attempt_count"], 1)
            self.assertIsNotNone(states[0]["last_sent_at"])
            second = dispatch_reminder(
                {
                    "reminder_id": reminder_id,
                    "target_user_id": member_id,
                    "channel": "INTERNAL",
                    "idempotency_key": key,
                },
                actor_id=owner_id,
            )
            self.assertTrue(second[0]["replayed"])
            self.assertEqual(second[0]["id"], first[0]["id"])
            self.assertEqual(execution_log_count(reminder_id), 1)
            logs = fetch_execution_logs(reminder_id, limit=10, offset=0)
            self.assertEqual(len(logs), 1)
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT title, COUNT(*) FROM notifications
                        WHERE user_id = %s AND message = %s
                        GROUP BY title
                        """,
                        [member_id, _MESSAGE],
                    )
                    row = cursor.fetchone()
                    self.assertEqual(row[1], 1)
                    self.assertEqual(row[0], title)
            finally:
                connection.close()
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            delete_temp_user(member_id)
            delete_temp_user(owner_id)

    def test_send_external_has_log_without_notification(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-خارجی")
        contact_id = insert_external_contact(
            {"name": unique_contact_name(), "phone": unique_phone()}
        )
        reminder_id = None
        try:
            reminder_id = insert_reminder(
                {
                    "title": unique_reminder_title(),
                    "message_template": _MESSAGE,
                    "scheduled_at": _WHEN,
                    "reminder_type": "یک‌باره",
                    "frequency": "یک‌باره",
                    "target_external_contact_id": contact_id,
                },
                created_by=owner_id,
            )
            sent = dispatch_reminder(
                {
                    "reminder_id": reminder_id,
                    "target_external_contact_id": contact_id,
                    "channel": "INTERNAL",
                },
                actor_id=owner_id,
            )
            self.assertEqual(sent[0]["external_contact_id"], contact_id)
            self.assertIsNone(sent[0]["user_id"])
            self.assertIsNone(sent[0].get("notification_id"))
            self.assertEqual(execution_log_count(reminder_id), 1)
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            delete_temp_external_contact(contact_id)
            delete_temp_user(owner_id)

    def test_retry_without_send_and_telegram_are_invalid(self) -> None:
        owner_id = insert_temp_user(last_name="سازنده-retry")
        reminder_id = None
        try:
            reminder_id = insert_reminder(
                {
                    "title": unique_reminder_title(),
                    "message_template": _MESSAGE,
                    "scheduled_at": _WHEN,
                    "reminder_type": "یک‌باره",
                    "frequency": "یک‌باره",
                    "target_user_id": owner_id,
                },
                created_by=owner_id,
            )
            with self.assertRaises(InvalidInputError) as retry_exc:
                dispatch_reminder(
                    {"reminder_id": reminder_id, "channel": "INTERNAL"},
                    actor_id=owner_id,
                    retry=True,
                )
            self.assertEqual(retry_exc.exception.error_code, INVALID_INPUT)
            with self.assertRaises(InvalidInputError) as channel_exc:
                dispatch_reminder(
                    {"reminder_id": reminder_id, "channel": "TELEGRAM"},
                    actor_id=owner_id,
                )
            self.assertEqual(channel_exc.exception.error_code, INVALID_INPUT)
        finally:
            if reminder_id is not None:
                delete_temp_reminder(reminder_id)
            delete_temp_user(owner_id)


if __name__ == "__main__":
    unittest.main()
