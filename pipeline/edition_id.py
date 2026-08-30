"""
WORLD PULSE v6 - Edition ID

Provides deterministic identifiers for publication editions.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_LANGUAGE = "en"


def build_edition_id(
    publication_date: date | datetime | str,
    edition_time: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    timezone: str = DEFAULT_TIMEZONE,
) -> str:
    """
    Build a stable Edition ID.

    Example:
        WORLD-PULSE-EN-2026-08-30-0700
    """

    if not language or not isinstance(language, str):
        raise ValueError("language must be a non-empty string")

    if not isinstance(edition_time, str):
        raise ValueError("edition_time must be a string")

    try:
        hour, minute = (
            part.strip()
            for part in edition_time.split(":", 1)
        )

        hour = int(hour)
        minute = int(minute)

    except (AttributeError, TypeError, ValueError):
        raise ValueError(
            "edition_time must use HH:MM format"
        )

    if not (0 <= hour <= 23):
        raise ValueError(
            "edition_time hour must be 00-23"
        )

    if not (0 <= minute <= 59):
        raise ValueError(
            "edition_time minute must be 00-59"
        )

    try:
        timezone_info = ZoneInfo(timezone)
    except Exception as exc:
        raise ValueError(
            f"invalid timezone: {timezone}"
        ) from exc

    if isinstance(publication_date, datetime):
        local_date = publication_date.astimezone(
            timezone_info
        ).date()

    elif isinstance(publication_date, date):
        local_date = publication_date

    elif isinstance(publication_date, str):
        try:
            local_date = date.fromisoformat(
                publication_date.strip()
            )
        except ValueError as exc:
            raise ValueError(
                "publication_date must use YYYY-MM-DD format"
            ) from exc

    else:
        raise ValueError(
            "publication_date must be date, datetime, or YYYY-MM-DD"
        )

    normalized_language = language.strip().upper()

    if not normalized_language:
        raise ValueError(
            "language must be a non-empty string"
        )

    return (
        f"WORLD-PULSE-"
        f"{normalized_language}-"
        f"{local_date.isoformat()}-"
        f"{hour:02d}{minute:02d}"
    )
