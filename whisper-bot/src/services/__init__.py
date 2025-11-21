"""Services package."""

from .whisper import WhisperService
from .gpt import GPTService, ProcessingType
from .media import MediaProcessor

try:
    from .calendar import (
        extract_meeting_info,
        format_meeting_summary,
        create_ics_file,
        create_google_calendar_event,
        check_calendar_auth,
    )
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

__all__ = [
    "WhisperService",
    "GPTService",
    "ProcessingType",
    "MediaProcessor",
    "CALENDAR_AVAILABLE",
]

if CALENDAR_AVAILABLE:
    __all__.extend([
        "extract_meeting_info",
        "format_meeting_summary",
        "create_ics_file",
        "create_google_calendar_event",
        "check_calendar_auth",
    ])
