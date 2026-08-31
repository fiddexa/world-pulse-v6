"""
WORLD PULSE v6 - Edition Publication Layer

Builds a deterministic, channel-specific publication package
from an already-built WORLD PULSE edition.

This layer:
- does not collect news;
- does not rewrite events;
- does not change editorial decisions;
- does not change verification;
- does not perform delivery;
- does not publish externally.

It converts an edition-level structure into a complete
Telegram publication package.
"""

from datetime import datetime
from typing import Any


TELEGRAM = "telegram"


SECTION_ORDER = (
    "world",
    "geopolitics",
    "business",
    "economy",
    "markets",
    "technology",
    "science",
    "health",
    "culture",
    "sports",
)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return []


def _content(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("content")

    if isinstance(value, dict):
        return value

    return {}


def _publication(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("publication")

    if isinstance(value, dict):
        return value

    return {}


def _telegram_text(event: Any) -> str:
    """
    Return the already-prepared event-level Telegram text.

    Edition publication does not rewrite event content.
    """
    return _safe_text(
        _publication(event).get("telegram")
    )


def _event_title(event: Any) -> str:
    return _safe_text(
        _content(event).get("headline")
    )


def _event_section(event: Any) -> str:
    return (
        _safe_text(
            _content(event).get("section")
        ).lower()
        or "world"
    )


def _event_role(event: Any) -> str:
    if not isinstance(event, dict):
        return "BRIEF"

    editorial = event.get("editorial")

    if isinstance(editorial, dict):
        role = _safe_text(
            editorial.get("role")
        )

        if role:
            return role.upper()

    return "BRIEF"


def _event_block(event: Any) -> dict:
    """
    Build deterministic event metadata for the edition package.

    The original event remains untouched.
    """
    return {
        "role": _event_role(event),
        "section": _event_section(event),
        "headline": _event_title(event),
        "telegram": _telegram_text(event),
    }


def _edition_events(edition: Any) -> list:
    if not isinstance(edition, dict):
        return []

    events = []

    top_story = edition.get("top_story")

    if isinstance(top_story, dict):
        events.append(top_story)

    for key in ("main_stories", "briefs"):
        for event in _safe_list(
            edition.get(key)
        ):
            if isinstance(event, dict):
                events.append(event)

    return events


def _edition_datetime(edition: dict) -> str:
    """
    Resolve a human-readable edition date/time.

    Uses edition_time/date when available.
    """
    edition_date = _safe_text(
        edition.get("edition_date")
    )

    edition_time = _safe_text(
        edition.get("edition_time")
    )

    if edition_date and edition_time:
        return f"{edition_date} · {edition_time}"

    if edition_date:
        return edition_date

    return ""


def _build_header(edition: dict) -> str:
    edition_datetime = _edition_datetime(edition)

    parts = ["🌍 WORLD PULSE"]

    if edition_datetime:
        parts.append(edition_datetime)

    return "\n".join(parts)


def _build_section_header(section: str) -> str:
    return section.replace(
        "_",
        " ",
    ).upper()


def _build_story_block(event: dict) -> str:
    telegram = _telegram_text(event)

    if not telegram:
        return ""

    return telegram


def _build_top_story(events: list) -> str:
    for event in events:
        if _event_role(event) == "TOP_STORY":
            block = _build_story_block(event)

            if block:
                return (
                    "TOP STORY\n"
                    "━━━━━━━━━━━━\n\n"
                    f"{block}"
                )

    return ""


def _build_section_blocks(events: list) -> list:
    """
    Group non-top-story events by section.

    Known sections follow the canonical SECTION_ORDER.
    Unknown sections are appended alphabetically.
    """
    grouped = {}

    for event in events:
        if _event_role(event) == "TOP_STORY":
            continue

        telegram = _telegram_text(event)

        if not telegram:
            continue

        section = _event_section(event)

        grouped.setdefault(
            section,
            [],
        ).append(event)

    if not grouped:
        return []

    ordered_sections = []

    for section in SECTION_ORDER:
        if section in grouped:
            ordered_sections.append(section)

    for section in sorted(grouped):
        if section not in ordered_sections:
            ordered_sections.append(section)

    blocks = []

    for section in ordered_sections:
        stories = []

        for event in grouped[section]:
            block = _build_story_block(event)

            if block:
                stories.append(block)

        if not stories:
            continue

        blocks.append(
            _build_section_header(section)
            + "\n"
            + "━━━━━━━━━━━━\n\n"
            + "\n\n".join(stories)
        )

    return blocks


def _build_telegram_text(
    edition: dict,
    events: list,
) -> str:
    """
    Build the complete editorial Telegram edition.

    Event-level publication text is reused exactly as prepared
    by the publication layer.
    """
    parts = [
        _build_header(edition)
    ]

    top_story = _build_top_story(events)

    if top_story:
        parts.append(top_story)

    parts.extend(
        _build_section_blocks(events)
    )

    return "\n\n".join(
        part
        for part in parts
        if _safe_text(part)
    )


def build_edition_publication(
    edition: Any,
) -> dict:
    """
    Build an edition-level publication package.

    The original edition is never modified.
    """
    if not isinstance(edition, dict):
        return {}

    events = _edition_events(edition)

    telegram_events = [
        _event_block(event)
        for event in events
        if _telegram_text(event)
    ]

    telegram_text = _build_telegram_text(
        edition,
        events,
    )

    return {
        "edition_id": _safe_text(
            edition.get("edition_id")
        ),
        "edition_type": _safe_text(
            edition.get("edition_type")
        ) or "WORLD_PULSE",
        "event_count": len(events),
        "telegram": {
            "channel": TELEGRAM,
            "text": telegram_text,
            "event_count": len(telegram_events),
            "events": telegram_events,
        },
    }


def build_edition_publications(
    editions: Any,
) -> list:
    """
    Build publication packages for multiple editions.
    """
    if not isinstance(editions, list):
        return []

    return [
        build_edition_publication(edition)
        for edition in editions
        if isinstance(edition, dict)
    ]
