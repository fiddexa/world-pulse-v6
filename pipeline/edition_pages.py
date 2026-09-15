"""
AROUND THE MAIN — Edition Page Manager

Builds the logical page structure of one newspaper edition.

Responsibilities:
- PAGE 01 is always the front page;
- additional pages are created only when there is real content;
- no editorial rewriting;
- no ranking;
- no image downloading;
- no external publication.

This module describes WHAT belongs on each page.
The newspaper renderer decides HOW each page looks.
"""

from dataclasses import dataclass, field
from typing import Any


# =====================================================================
# PAGE TYPES
# =====================================================================

PAGE_FRONT = "FRONT_PAGE"
PAGE_WORLD = "WORLD"
PAGE_BUSINESS = "BUSINESS"
PAGE_TECHNOLOGY = "TECHNOLOGY"
PAGE_ECONOMY = "ECONOMY"
PAGE_SCIENCE = "SCIENCE"
PAGE_HEALTH = "HEALTH"
PAGE_SPORTS = "SPORTS"


@dataclass
class EditionPage:
    """
    One logical newspaper page.
    """

    page_number: int
    page_type: str
    title: str
    events: list[dict[str, Any]] = field(
        default_factory=list
    )

    @property
    def page_label(self) -> str:
        return f"PAGE {self.page_number:02d}"

    @property
    def is_empty(self) -> bool:
        return len(self.events) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "page_label": self.page_label,
            "page_type": self.page_type,
            "title": self.title,
            "events": self.events,
        }


# =====================================================================
# HELPERS
# =====================================================================

def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return []


def _event_category(event: dict[str, Any]) -> str:
    """
    Read category without changing the event.

    Different pipeline stages may store the category
    under slightly different keys.
    """

    for key in (
        "category",
        "section",
        "topic",
    ):
        value = event.get(key)

        if value:
            return str(value).strip().lower()

    content = event.get("content")

    if isinstance(content, dict):
        for key in (
            "category",
            "section",
            "topic",
        ):
            value = content.get(key)

            if value:
                return str(value).strip().lower()

    return ""


def _category_page_type(category: str) -> str | None:
    category = category.lower().strip()

    mapping = {
        "world": PAGE_WORLD,
        "geopolitics": PAGE_WORLD,
        "business": PAGE_BUSINESS,
        "technology": PAGE_TECHNOLOGY,
        "tech": PAGE_TECHNOLOGY,
        "economy": PAGE_ECONOMY,
        "science": PAGE_SCIENCE,
        "health": PAGE_HEALTH,
        "sports": PAGE_SPORTS,
        "sport": PAGE_SPORTS,
    }

    return mapping.get(category)


def _page_title(page_type: str) -> str:
    titles = {
        PAGE_FRONT: "FRONT PAGE",
        PAGE_WORLD: "WORLD",
        PAGE_BUSINESS: "BUSINESS",
        PAGE_TECHNOLOGY: "TECHNOLOGY",
        PAGE_ECONOMY: "ECONOMY",
        PAGE_SCIENCE: "SCIENCE",
        PAGE_HEALTH: "HEALTH",
        PAGE_SPORTS: "SPORTS",
    }

    return titles.get(
        page_type,
        page_type,
    )


# =====================================================================
# PAGE BUILDER
# =====================================================================


def build_edition_pages(
    edition: dict[str, Any],
) -> list[EditionPage]:
    """
    Build physical newspaper pages from the single ordered Edition stream.

    Page 01 and all later pages use the same editorial sequence.
    The renderer decides the visual geometry; this layer decides only
    which stories belong to which physical page stream.
    """

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    pages: list[EditionPage] = []

    # ================================================================
    # ONE ORDERED EDITORIAL STREAM
    # ================================================================

    ordered = [
        event
        for event in (
            edition.get("ordered")
            or []
        )
        if isinstance(event, dict)
    ]

    # Backward-compatible fallback for older Edition Models.
    if not ordered:
        fallback = []

        top_story = edition.get(
            "top_story"
        )

        if isinstance(top_story, dict):
            fallback.append(
                top_story
            )

        for key in (
            "main_stories",
            "briefs",
        ):
            values = edition.get(
                key
            )

            if isinstance(values, list):
                fallback.extend(
                    event
                    for event in values
                    if isinstance(
                        event,
                        dict,
                    )
                )

        ordered = fallback

    # ================================================================
    # PAGE 01
    # ================================================================

    front_events = ordered[:5]

    pages.append(
        EditionPage(
            page_number=1,
            page_type=PAGE_FRONT,
            title=_page_title(
                PAGE_FRONT
            ),
            events=list(
                front_events
            ),
        )
    )

    # ================================================================
    # REMAINING EVENTS
    # ================================================================

    remaining = ordered[5:]

    if not remaining:
        return pages

    # ================================================================
    # GROUP REMAINING STORIES INTO CATEGORY STREAMS
    # ================================================================

    category_order = [
        PAGE_WORLD,
        PAGE_BUSINESS,
        PAGE_TECHNOLOGY,
        PAGE_ECONOMY,
        PAGE_SCIENCE,
        PAGE_HEALTH,
        PAGE_SPORTS,
    ]

    groups: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for event in remaining:

        category = _event_category(
            event
        )

        page_type = _category_page_type(
            category
        )

        if page_type is None:
            page_type = PAGE_WORLD

        groups.setdefault(
            page_type,
            [],
        ).append(event)

    # ================================================================
    # DENSE PAGE STREAM
    # ================================================================

    page_number = 2

    current_events: list[
        dict[str, Any]
    ] = []

    current_types: list[str] = []

    def flush_page():
        nonlocal page_number
        nonlocal current_events
        nonlocal current_types

        if not current_events:
            return

        unique_types = []

        for item in current_types:
            if item not in unique_types:
                unique_types.append(
                    item
                )

        if len(unique_types) == 1:
            page_type = unique_types[0]
            title = _page_title(
                page_type
            )
        else:
            page_type = "MIXED"
            title = "GLOBAL NEWS"

        pages.append(
            EditionPage(
                page_number=page_number,
                page_type=page_type,
                title=title,
                events=list(
                    current_events
                ),
            )
        )

        page_number += 1
        current_events = []
        current_types = []

    # Preserve ordered sequence.
    for event in remaining:

        page_type = _category_page_type(
            _event_category(event)
        )

        if page_type is None:
            page_type = PAGE_WORLD

        current_events.append(
            event
        )

        current_types.append(
            page_type
        )

        # Keep the physical stream dense.
        # The renderer's page planner performs the actual geometry.
        if len(current_events) >= 7:
            flush_page()

    flush_page()

    return pages
