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

from typing import Any


TELEGRAM = "telegram"


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


def _telegram_text(event: Any) -> str:
    """
    Return the already-prepared event-level Telegram text.

    Edition publication does not rewrite the event content.
    """
    if not isinstance(event, dict):
        return ""

    publication = event.get("publication")

    if isinstance(publication, dict):
        value = _safe_text(publication.get("telegram"))

        if value:
            return value

    return ""


def _event_title(event: Any) -> str:
    content = _content(event)

    return _safe_text(content.get("headline"))


def _event_section(event: Any) -> str:
    content = _content(event)

    return _safe_text(content.get("section")) or "world"


def _event_role(event: Any) -> str:
    if not isinstance(event, dict):
        return "BRIEF"

    editorial = event.get("editorial")

    if isinstance(editorial, dict):
        role = _safe_text(editorial.get("role"))

        if role:
            return role.upper()

    return "BRIEF"


def _event_block(event: Any) -> dict:
    """
    Build a deterministic event reference for the edition package.

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
        for event in _safe_list(edition.get(key)):
            if isinstance(event, dict):
                events.append(event)

    return events


def _build_header(edition: dict) -> str:
    edition_id = _safe_text(edition.get("edition_id"))

    if edition_id:
        return f"WORLD PULSE\nEdition {edition_id}"

    return "WORLD PULSE"


def _build_section_header(section: str) -> str:
    return section.replace("_", " ").upper()


def _build_telegram_text(edition: dict, events: list) -> str:
    """
    Build the complete Telegram edition text.

    Event-level publication text is reused exactly as prepared
    by the publication layer.
    """
    parts = [_build_header(edition)]

    current_section = None

    for event in events:
        section = _event_section(event)

        if section != current_section:
            current_section = section
            parts.append(_build_section_header(section))

        telegram = _telegram_text(event)

        if telegram:
            parts.append(telegram)

    return "\n\n".join(
        part
        for part in parts
        if _safe_text(part)
    )


def build_edition_publication(edition: Any) -> dict:
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


def build_edition_publications(editions: Any) -> list:
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
