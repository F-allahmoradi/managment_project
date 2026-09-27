"""شرکت‌کنندهٔ جلسه: قانون XOR مثل گیرندهٔ پیام.

هر ردیف دقیقاً یکی از user یا external_contact است.
"""

from errors.crud import InvalidInputError
from logging_module import logged_step
from repository.db import run_query
from services.audit_log import ACTION_CREATE, record_audit_on
from services.external_contact import fetch_external_contact
from services.user import fetch_user

from business_logic.meetings import require_meeting_access, require_meeting_manager
from business_logic.repository import UNIQUE_MESSAGES, insert_participant_on


def assert_one_target(user_id, external_contact_id) -> None:
    """اگر هر دو پر یا هر دو خالی باشند قبل از INSERT خطا می‌دهد."""
    has_user = user_id is not None
    has_external = external_contact_id is not None
    if has_user == has_external:
        raise InvalidInputError(
            "شرکت‌کننده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
        )


def prepare_target(user_id, external_contact_id) -> dict:
    """هدف را با XOR و وجود ردیف می‌سنجد."""
    assert_one_target(user_id, external_contact_id)
    if user_id is not None:
        user = fetch_user(user_id)
        if not user["is_active"]:
            raise InvalidInputError("کاربر غیرفعال نمی‌تواند شرکت‌کننده باشد")
        return {"user_id": user_id, "external_contact_id": None}
    contact = fetch_external_contact(external_contact_id)
    if not contact["is_active"]:
        raise InvalidInputError("مخاطب خارجی غیرفعال است")
    return {"user_id": None, "external_contact_id": external_contact_id}


def insert_participant(fields: dict, actor_id: int) -> int:
    """یک شرکت‌کننده با قانون XOR به جلسه موجود اضافه می‌کند."""
    meeting = require_meeting_access(actor_id, fields["meeting_id"])
    require_meeting_manager(actor_id, meeting)
    prepared = prepare_target(fields.get("user_id"), fields.get("external_contact_id"))
    payload = {
        "meeting_id": fields["meeting_id"],
        "user_id": prepared["user_id"],
        "external_contact_id": prepared["external_contact_id"],
        "role": fields.get("role"),
    }

    def work(connection):
        new_id = insert_participant_on(connection, payload)
        record_audit_on(
            connection,
            actor_id,
            ACTION_CREATE,
            "MeetingParticipant",
            new_id,
            None,
            {
                "meeting_id": payload["meeting_id"],
                "user_id": payload["user_id"],
                "external_contact_id": payload["external_contact_id"],
            },
        )
        return new_id

    return run_query(work, UNIQUE_MESSAGES)


assert_one_target = logged_step("validate")(assert_one_target)
insert_participant = logged_step("insert")(insert_participant)
