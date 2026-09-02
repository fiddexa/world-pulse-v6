"""
AROUND THE MAIN v6 - Edition Slot Resolver

Resolves the active AROUND THE MAIN edition slot for a given moment.

The resolver always operates in the canonical production timezone:
America/New_York.

It does not schedule, build, or publish editions.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from pipeline.edition_id import (
    DEFAULT_LANGUAGE,
    DEFAULT_TIMEZONE,
    build_edition_id,
)
from pipeline.edition_slots import EDITION_SLOTS


TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE)


def _slot_time(edition_time: str) -> time:
    hour, minute = (
        int(part)
        for part in edition_time.split(":", 1)
    )

    return time(
        hour=hour,
        minute=minute,
    )


def resolve_edition_slot(
    current_time: datetime,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> dict:
    """
    Resolve the latest active edition slot.

    The supplied datetime may be timezone-aware or naive.

    Naive datetimes are interpreted as America/New_York local time.
    Timezone-aware datetimes are converted to America/New_York.
    """

    if not isinstance(current_time, datetime):
        raise ValueError(
            "current_time must be a datetime"
        )

    if current_time.tzinfo is None:
        local_time = current_time.replace(
            tzinfo=TIMEZONE
        )
    else:
        local_time = current_time.astimezone(
            TIMEZONE
        )

    current_clock = local_time.time()

    selected_slot = None

    for edition_time in EDITION_SLOTS:
        if current_clock >= _slot_time(edition_time):
            selected_slot = edition_time

    if selected_slot is None:
        edition_date = (
            local_time.date()
            - timedelta(days=1)
        )
        selected_slot = EDITION_SLOTS[-1]
    else:
        edition_date = local_time.date()

    edition_id = build_edition_id(
        edition_date,
        selected_slot,
        language=language,
        timezone=DEFAULT_TIMEZONE,
    )

    return {
        "edition_date": edition_date.isoformat(),
        "edition_time": selected_slot,
        "edition_id": edition_id,
    }
