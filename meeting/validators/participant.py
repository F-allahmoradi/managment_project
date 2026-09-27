"""اعتبارسنجی ورودی افزودن شرکت‌کننده."""

from logging_module import logged_step


def validate_create_meeting_participant(fields: dict) -> dict:
    """ورودی افزودن شرکت‌کننده را با اسکیما بررسی می‌کند؛ XOR در مدل است."""
    from schemas.meeting.participant import CreateMeetingParticipantInput

    return CreateMeetingParticipantInput(**fields).model_dump()


validate_create_meeting_participant = logged_step("validate")(
    validate_create_meeting_participant
)
