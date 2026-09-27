"""ارسال واقعی یادآوری روی کانال INTERNAL و نوشتن execution_logs."""

from datetime import datetime

from errors.crud import InvalidInputError
from logging_module import logged_step
from repository.db import run_query

from business_logic.channels.internal import deliver_internal
from business_logic.follow_up import (
    assert_one_target,
    fetch_reminder,
    require_reminder_write,
)
from business_logic.repository import (
    UNIQUE_MESSAGES,
    fetch_execution_log_by_key_on,
    fetch_execution_log_records,
    fetch_follow_up_state_records_on,
    insert_execution_log_on,
    lock_reminder_on,
    mark_follow_up_sent_on,
    mark_reminder_ran_on,
    max_attempt_number_on,
)

INTERNAL_CHANNEL = "INTERNAL"
ALLOWED_CHANNELS = {INTERNAL_CHANNEL}
ACTIVE_STATUS = "فعال"


def default_idempotency_key(
    reminder_id: int,
    user_id,
    external_contact_id,
    channel: str,
    attempt_number: int,
) -> str:
    """کلید پایدار یک تلاش ارسال برای یک گیرنده را می‌سازد."""
    if user_id is not None:
        target = f"user:{user_id}"
    else:
        target = f"external:{external_contact_id}"
    return f"reminder:{reminder_id}:{target}:{channel}:{attempt_number}"


def _normalize_channel(channel) -> str:
    name = INTERNAL_CHANNEL if channel is None else str(channel).strip()
    if name not in ALLOWED_CHANNELS:
        raise InvalidInputError("در این گام فقط کانال INTERNAL مجاز است")
    return name


def _select_targets(states: list, user_id, external_id) -> list:
    """گیرنده‌های ارسال را از follow_up_states جدا می‌کند."""
    if user_id is None and external_id is None:
        return list(states)
    assert_one_target(user_id, external_id)
    matched = []
    for state in states:
        if user_id is not None and state.get("user_id") == user_id:
            matched.append(state)
        if (
            external_id is not None
            and state.get("external_contact_id") == external_id
        ):
            matched.append(state)
    if not matched:
        raise InvalidInputError("این گیرنده برای این یادآوری نیست")
    return matched


def _with_replay_flag(row: dict, replayed: bool) -> dict:
    payload = dict(row)
    payload["replayed"] = replayed
    return payload


def _dispatch_one_on(
    connection,
    reminder: dict,
    state: dict,
    channel: str,
    retry: bool,
    custom_key,
) -> dict:
    """یک گیرنده را روی اتصال قفل‌شده می‌فرستد یا همان لاگ قبلی را برمی‌گرداند."""
    reminder_id = reminder["id"]
    user_id = state.get("user_id")
    external_id = state.get("external_contact_id")
    previous = max_attempt_number_on(
        connection,
        reminder_id,
        user_id,
        external_id,
        channel,
    )
    if retry:
        if previous < 1:
            raise InvalidInputError("برای retry باید یک بار send_reminder شده باشد")
        attempt_number = previous + 1
    else:
        attempt_number = 1
    key = custom_key or default_idempotency_key(
        reminder_id,
        user_id,
        external_id,
        channel,
        attempt_number,
    )
    existing = fetch_execution_log_by_key_on(connection, key)
    if existing is not None:
        return _with_replay_flag(existing, True)
    delivered = deliver_internal(connection, reminder, state)
    sent_at = datetime.utcnow()
    row = insert_execution_log_on(
        connection,
        {
            "reminder_id": reminder_id,
            "user_id": user_id,
            "external_contact_id": external_id,
            "channel": channel,
            "rendered_message": delivered["rendered_message"],
            "status": "SENT",
            "attempt_number": attempt_number,
            "scheduled_for": reminder.get("scheduled_at"),
            "sent_at": sent_at,
            "error_message": None,
            "idempotency_key": key,
        },
    )
    mark_follow_up_sent_on(connection, state["id"])
    mark_reminder_ran_on(connection, reminder_id)
    payload = _with_replay_flag(row, False)
    payload["notification_id"] = delivered["notification_id"]
    return payload


def dispatch_reminder(fields: dict, actor_id: int, retry: bool = False) -> list:
    """یادآوری فعال را برای گیرنده‌ها روی INTERNAL می‌فرستد.

    کلید idempotency اگر از قبل باشد، اعلان و لاگ جدید ساخته نمی‌شود.
    """
    reminder_id = fields["reminder_id"]
    reminder = fetch_reminder(reminder_id)
    require_reminder_write(actor_id, reminder)
    if reminder.get("status_name") != ACTIVE_STATUS:
        raise InvalidInputError("فقط یادآوری فعال ارسال می‌شود")
    channel = _normalize_channel(fields.get("channel"))
    target_user_id = fields.get("target_user_id")
    target_external_id = fields.get("target_external_contact_id")
    custom_key = fields.get("idempotency_key")
    if custom_key and target_user_id is None and target_external_id is None:
        raise InvalidInputError(
            "کلید idempotency فقط وقتی مجاز است که یک گیرنده مشخص باشد"
        )

    def work(connection):
        lock_reminder_on(connection, reminder_id)
        states = fetch_follow_up_state_records_on(connection, reminder_id)
        targets = _select_targets(states, target_user_id, target_external_id)
        if not targets:
            raise InvalidInputError("گیرنده‌ای برای ارسال نیست")
        if custom_key and len(targets) != 1:
            raise InvalidInputError(
                "کلید idempotency فقط برای یک گیرنده مجاز است"
            )
        results = []
        for state in targets:
            results.append(
                _dispatch_one_on(
                    connection,
                    reminder,
                    state,
                    channel,
                    retry,
                    custom_key,
                )
            )
        return results

    return run_query(work, UNIQUE_MESSAGES)


def fetch_execution_logs(reminder_id: int, limit: int, offset: int) -> list:
    """لاگ ارسال یک یادآوری را می‌خواند."""
    fetch_reminder(reminder_id)
    return fetch_execution_log_records(reminder_id, limit, offset)


dispatch_reminder = logged_step("insert")(dispatch_reminder)
fetch_execution_logs = logged_step("fetch")(fetch_execution_logs)
