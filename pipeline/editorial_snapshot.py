"""
AROUND THE MAIN v6 - Editorial Snapshot

Defines the time boundary for a single edition's editorial view.

The snapshot answers one question:

    Was this information available to AROUND THE MAIN by the time
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


def _timestamp_group(event: dict, key: str) -> list[datetime]:
    dates: list[datetime] = []

    direct = _parse_datetime(event.get(key))
    if direct is not None:
        dates.append(direct)

    for article in _articles(event):
        value = _parse_datetime(article.get(key))
        if value is not None:
            dates.append(value)

    return dates


def _availability_dates(event: dict) -> list[datetime]:
    """
    Return the best available AROUND THE MAIN information timestamps.

    Timestamp precedence is deliberate:

    1. first_seen_at
    2. available_at
    3. published_at

    Lower-priority timestamps are not mixed into a higher-priority
    group. This prevents an old published_at value from contradicting
    an explicit first_seen_at value.
    """

    for key in (
        "first_seen_at",
        "available_at",
        "published_at",
    ):
        dates = _timestamp_group(event, key)
        if dates:
            return dates

    return []


def first_known_at(event: Any) -> datetime | None:
    """
    Return the earliest timestamp from the highest available
    information-availability tier.

    This is deliberately different from event_time. An event may occur
    before AROUND THE MAIN receives reliable information about it.
    """

    if not isinstance(event, dict):
        return None

    dates = _availability_dates(event)
    if not dates:
        return None

    return min(dates)


def last_known_at(event: Any) -> datetime | None:
    """Return the latest timestamp from the selected availability tier."""

    if not isinstance(event, dict):
        return None

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


def filter_events_for_snapshot(
    events: Any,
    editorial_time: datetime,
    *,
    include_unknown: bool = False,
) -> list[dict]:
    """
    Return events eligible for a specific editorial snapshot.

    Unknown availability is excluded by default. Production ingestion
    should provide first_seen_at whenever possible; include_unknown is
    available for controlled compatibility paths and tests.
    """

    if not isinstance(events, list):
        return []

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        status = snapshot_status(event, editorial_time)

        if status == SNAPSHOT_ELIGIBLE:
            results.append(dict(event))
        elif status == SNAPSHOT_UNKNOWN and include_unknown:
            results.append(dict(event))

    return results


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

    snapshot = _parse_datetime(editorial_time)
    if snapshot is None:
        raise ValueError("editorial_time must be a valid datetime")

    result = dict(event)
    status = snapshot_status(event, editorial_time)
    known = first_known_at(event)
    updated = last_known_at(event)

    result["editorial_snapshot"] = {
        "status": status,
        "editorial_time": snapshot.isoformat(),
        "first_known_at": known.isoformat() if known else None,
        "last_known_at": updated.isoformat() if updated else None,
    }

    return result
