"""Calendar service for event creation and management."""

from .parser import extract_meeting_info, format_meeting_summary
from .integration import create_ics_file, create_google_calendar_event, check_calendar_auth

__all__ = [
    "extract_meeting_info",
    "format_meeting_summary",
    "create_ics_file",
    "create_google_calendar_event",
    "check_calendar_auth",
]
