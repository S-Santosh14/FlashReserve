import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def format_booking_timestamp(value):
    if value is None or value == "":
        return "Unavailable"
    try:
        timestamp = value if isinstance(value, datetime) else datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        logger.warning("Booking timestamp has an invalid format.")
        return "Invalid timestamp"
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
