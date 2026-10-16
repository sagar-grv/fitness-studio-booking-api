"""Timezone helpers.

Rule from the brief: all class times are stored in IST and converted
appropriately for other timezones.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from .config import IST

IST_ZONE = ZoneInfo(IST)


def to_ist(dt: datetime) -> datetime:
    """Normalize a datetime to IST.

    Naive datetimes are assumed to already be in IST; aware datetimes
    are converted from their own offset.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST_ZONE)
    return dt.astimezone(IST_ZONE)


def serialize_ist(dt: datetime) -> str:
    """Serialize a datetime as an ISO-8601 string with the IST offset."""
    return to_ist(dt).isoformat()


def parse_stored(value: str) -> datetime:
    """Parse a stored IST ISO string back into an aware datetime."""
    return datetime.fromisoformat(value)


def convert_for_output(value: str, timezone: str) -> str:
    """Convert a stored IST time into the requested output timezone."""
    try:
        zone = ZoneInfo(timezone)
    except Exception:
        raise HTTPException(
            status_code=400, detail=f"Unknown timezone: {timezone!r}"
        )
    return parse_stored(value).astimezone(zone).isoformat()
