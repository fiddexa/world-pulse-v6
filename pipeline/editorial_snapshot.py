"""
WORLD PULSE v6 - Editorial Snapshot

Defines the time boundary for a single edition's editorial view.

The snapshot answers one question:

    Was this information available to WORLD PULSE by the time
    the edition was being prepared?

This layer does not decide whether an event is important. It only
establishes eligibility for a particular editorial snapshot.
"""

from datetime import datetime, timezone
from typing import Any


SNAPSHOT_ELIGIBLE = "ELIGIBLE"
SNAPSHOT_EXCLUDED = "EXCLUDED"
SNAPSHOT_UNKNOWN = "UNKNOWN"


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a supported timestamp into an aware UTC datetime."""

    if not value:
        return None

    if isinstance(value, datetime):
        result = value
    else:
        text = str(value).strip()
        if not text:
            return None

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            result = datetime.fromisoformat(text)
        except ValueError:
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def _articles(event: Any) -> list[dict]:
    if not isinstance(event, dict):
        return []

    value = event.get("articles")
    if not isinstance(value, list):
        return []

    return [
        article
        for article in value
        if isinstance(article, dict)
    ]


def _availability_dates(event: dict) -> list[datetime]:
    """
    Return known WORLD PULSE availability timestamps.

    Preferred order of evidence:

    1. event.first_seen_at
    2. article.first_seen_at
    3. article.available_at
    4. article.published_at

    published_at is a compatibility fallback for existing source data.
    New production ingestion should populate first_seen_at whenever
    the collection layer can establish it.
    """

    dates: list[datetime] = []

    direct = _parse_datetime(event.get("first_seen_at"))
    if direct is not None:
        dates.append(direct)

    direct = _parse_datetime(event.get("available_at"))
    if direct is not None:
        dates.append(direct)

    for article in _articles(event):
        for key in (
            "first_seen_at",
            "available_at",
            "published_at",
        ):
            value = _parse_datetime(article.get(key))
            if value is not None:
                dates.append(value)

    return dates


def first_known_at(event: Any) -> datetime | None:
    """
    Return the earliest known time at which the event was available.

    This is deliberately different from event_time. An event may occur
    before WORLD PULSE receives reliable information about it.
    """

    dates = _availability_dates(event)
    if not dates:
        return None

    return min(dates)


def last_known_at(event: Any) -> datetime | None:
    """Return the latest known source-information timestamp."""

    dates = _availability_dates(event)
    if not dates:
        return None

    return max(dates)


def snapshot_status(
    event: Any,
    editorial_time: datetime,
) -> str:
    """
    Determine whether an event is available for an editorial snapshot.

    An event is eligible when its first known information timestamp is
    at or before the editorial snapshot time.

    Missing timestamps return UNKNOWN rather than silently inventing
    availability.
    """

    if not isinstance(editorial_time, datetime):
        raise ValueError("editorial_time must be a datetime")

    snapshot = _parse_datetime(editorial_time)
    if snapshot is None:
        raise ValueError("editorial_time must be a valid datetime")

    known = first_known_at(event)
    if known is None:
        return SNAPSHOT_UNKNOWN

    if known <= snapshot:
        return SNAPSHOT_ELIGIBLE

    return SNAPSHOT_EXCLUDED


def is_snapshot_eligible(
    event: Any,
    editorial_time: datetime,
) -> bool:
    """Return True only when the event was known by editorial_time."""

    return snapshot_status(event, editorial_time) == SNAPSHOT_ELIGIBLE


def annotate_snapshot(
    event: Any,
    editorial_time: datetime,
) -> dict:
    """
    Return a copy of an event with snapshot metadata.

    The original event is never modified.
    """

    if not isinstance(event, dict):
        return {}

    result = dict(event)
    status = snapshot_status(event, editorial_time)
    known = first_known_at(event)
    updated = last_known_at(event)

    result["editorial_snapshot"] = {
        "status": status,
        "editorial_time": _parse_datetime(editorial_time).isoformat(),
        "first_known_at": known.isoformat() if known else None,
        "last_known_at": updated.isoformat() if updated else None,
    }

    return result
