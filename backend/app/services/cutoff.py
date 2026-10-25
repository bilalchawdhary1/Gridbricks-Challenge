import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")

# Assumption: day-ahead decision is made at ~09:00 UK time on D-1. Configurable.
DECISION_HOUR = int(os.getenv("DECISION_HOUR", "9"))
DECISION_MINUTE = int(os.getenv("DECISION_MINUTE", "0"))


def decision_cutoff(delivery_date: date) -> datetime:
    """Latest publish time usable for delivery_date: D-1 at decision time, in UTC."""
    local = datetime.combine(
        delivery_date - timedelta(days=1),
        time(DECISION_HOUR, DECISION_MINUTE),
        tzinfo=LONDON,
    )
    return local.astimezone(UTC)