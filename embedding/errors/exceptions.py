"""خطاهای دامنهٔ امبدینگ؛ تعریف اصلی در errors.crud است."""

from errors.crud import (
    CONFIG_ERROR,
    EMPTY_TRANSCRIPT,
    LLM_ERROR,
    MEETING_NOT_FOUND,
    ConfigError,
    EmptyTranscriptError,
    LlmError,
    MeetingNotFoundError,
)

__all__ = [
    "CONFIG_ERROR",
    "EMPTY_TRANSCRIPT",
    "LLM_ERROR",
    "MEETING_NOT_FOUND",
    "ConfigError",
    "EmptyTranscriptError",
    "LlmError",
    "MeetingNotFoundError",
]
