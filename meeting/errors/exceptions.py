"""خطاهای دامنهٔ جلسات؛ تعریف اصلی در errors.crud است."""

from errors.crud import (
    MEETING_NOT_FOUND,
    MEETING_PARTICIPANT_NOT_FOUND,
    MEETING_SCHEDULE_NOT_FOUND,
    MEETING_SLOT_CONFLICT,
    MeetingNotFoundError,
    MeetingParticipantNotFoundError,
    MeetingScheduleNotFoundError,
    MeetingSlotConflictError,
)

__all__ = [
    "MEETING_NOT_FOUND",
    "MEETING_PARTICIPANT_NOT_FOUND",
    "MEETING_SCHEDULE_NOT_FOUND",
    "MEETING_SLOT_CONFLICT",
    "MeetingNotFoundError",
    "MeetingParticipantNotFoundError",
    "MeetingScheduleNotFoundError",
    "MeetingSlotConflictError",
]
