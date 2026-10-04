"""Timezone-aware deadline evidence shared by platform adapters."""

from datetime import date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo


def deadline_passed(value, *, now=None, zone="Asia/Seoul"):
    """Return True/False, or None when a deadline cannot be interpreted.

    A date without a time remains open through that local calendar day.
    A naive timestamp uses the platform's declared timezone, never host time.
    """
    text = str(value or "").strip()
    tz = ZoneInfo(zone)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("verification time must have a timezone")
    match = re.fullmatch(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\.?", text)
    try:
        if match:
            day = date(*(int(x) for x in match.groups()))
            deadline = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
        else:
            deadline = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=tz)
    except (ValueError, OverflowError):
        return None
    return now >= deadline
