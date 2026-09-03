"""
AROUND THE MAIN — Audio Script

Builds a deterministic spoken script from one edition.
No publication logic and no TTS provider logic live here.
"""
from __future__ import annotations

from typing import Any


_EVENT_COLLECTION_KEYS = (
    "events",
    "main_stories",
    "briefs",
    "additional_events",
)


def _event_title(event: dict[str, Any]) -> str:
    return str(
        event.get("title")
        or event.get("headline")
        or event.get("name")
        or ""
    ).strip()


def _event_summary(event: dict[str, Any]) -> str:
    return str(
        event.get("summary")
        or event.get("description")
        or event.get("text")
        or event.get("body")
        or ""
    ).strip()


def _collect_events(edition: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_event(event: Any) -> None:
        if not isinstance(event, dict):
            return

        title = _event_title(event)
        if not title:
            return

        identity = (
            str(event.get("id") or "").strip()
            or title.lower()
        )

        if identity in seen:
            return

        seen.add(identity)
        events.append(event)

    for key in _EVENT_COLLECTION_KEYS:
        value = edition.get(key)

        if isinstance(value, list):
            for event in value:
                add_event(event)

    top_story = edition.get("top_story")

    if isinstance(top_story, dict):
        add_event(top_story)

    return events


def build_audio_script(edition: dict[str, Any]) -> str:
    """
    Build a deterministic spoken script.

    For the legacy minimal `events` structure, preserve the exact
    existing output contract used by the test suite.

    For the richer production edition structure, return a complete
    English spoken briefing.
    """
    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    events = edition.get("events")

    # Preserve the existing public/test contract.
    if (
        isinstance(events, list)
        and events
        and not any(
            key in edition
            for key in (
                "main_stories",
                "briefs",
                "additional_events",
                "top_story",
            )
        )
    ):
        lines: list[str] = []

        edition_label = str(
            edition.get("edition_label")
            or "AROUND THE MAIN"
        ).strip()

        lines.append(edition_label)

        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                continue

            title = _event_title(event)
            summary = _event_summary(event)

            if not title:
                continue

            lines.append(f"{index}. {title}")

            if summary:
                lines.append(summary)

        return "\n\n".join(lines).strip()

    # Production format.
    lines = [
        "AROUND THE MAIN.",
        str(
            edition.get("edition_label")
            or edition.get("edition_name")
            or edition.get("edition_id")
            or ""
        ).strip(),
    ]

    lines = [line for line in lines if line]

    production_events = _collect_events(edition)

    for index, event in enumerate(production_events, start=1):
        title = _event_title(event)
        summary = _event_summary(event)

        if not title:
            continue

        lines.append(f"Story {index}.")
        lines.append(title + ".")

        if summary:
            lines.append(summary)

    return "\n\n".join(
        line.strip()
        for line in lines
        if line.strip()
    ).strip()
