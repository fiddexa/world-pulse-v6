"""
WORLD PULSE v6 - Edition Runner

Runs one deterministic WORLD PULSE edition.

This layer:
- receives the edition date and time explicitly, or resolves them
  from a supplied current time;
- processes the supplied articles;
- builds the edition;
- records event usage in persistent Event Memory;
- protects edition execution with persistent Edition Memory.

It does not schedule future runs.
It does not publish externally.
It does not perform Telegram delivery.
"""

from datetime import datetime

from pipeline.app import build_edition_from_articles
from pipeline.edition_memory import (
    COMPLETED,
    RUNNING,
    EditionMemory,
)
from pipeline.edition_slot_resolver import resolve_edition_slot
from pipeline.event_memory import EventMemory


def run_edition(
    articles,
    publication_date=None,
    edition_time=None,
    *,
    current_time=None,
    event_memory=None,
    edition_memory=None,
    language="en",
):
    """
    Build one WORLD PULSE edition.

    Two identity modes are supported.

    Explicit mode:
        publication_date + edition_time

    Resolver mode:
        current_time

    Edition Memory prevents the same Edition ID from being
    executed more than once.

    Returns:
        edition dictionary on successful execution;
        None when the Edition ID was already started/completed.
    """

    if current_time is not None:
        if (
            publication_date is not None
            or edition_time is not None
        ):
            raise ValueError(
                "current_time cannot be combined with "
                "publication_date or edition_time"
            )

        resolved = resolve_edition_slot(
            current_time,
            language=language,
        )

        publication_date = resolved["edition_date"]
        edition_time = resolved["edition_time"]

    if (
        publication_date is None
        or edition_time is None
    ):
        raise ValueError(
            "publication_date and edition_time are required "
            "unless current_time is supplied"
        )

    if event_memory is None:
        event_memory = EventMemory()

    if edition_memory is None:
        edition_memory = EditionMemory()

    from datetime import datetime

from pipeline.app import build_edition_from_articles
from pipeline.edition_id import build_edition_id
from pipeline.edition_memory import EditionMemory
from pipeline.edition_slot_resolver import resolve_edition_slot
from pipeline.event_memory import EventMemory


def run_edition(
    articles,
    publication_date=None,
    edition_time=None,
    *,
    current_time=None,
    event_memory=None,
    edition_memory=None,
    language="en",
):
    """
    Build one WORLD PULSE edition with persistent
    edition-level idempotency protection.
    """

    if current_time is not None:
        if (
            publication_date is not None
            or edition_time is not None
        ):
            raise ValueError(
                "current_time cannot be combined with "
                "publication_date or edition_time"
            )

        resolved = resolve_edition_slot(
            current_time,
            language=language,
        )

        publication_date = resolved["edition_date"]
        edition_time = resolved["edition_time"]

    if (
        publication_date is None
        or edition_time is None
    ):
        raise ValueError(
            "publication_date and edition_time are required "
            "unless current_time is supplied"
        )

    if event_memory is None:
        event_memory = EventMemory()

    if edition_memory is None:
        edition_memory = EditionMemory()

    edition_id = build_edition_id(
        publication_date,
        edition_time,
        language=language,
    )

    if not edition_memory.start(edition_id):
        return None

    try:
        edition = build_edition_from_articles(
            articles,
            publication_date=publication_date,
            edition_time=edition_time,
            event_memory=event_memory,
        )

        edition_memory.complete(edition_id)

        return edition

    except Exception:
        edition_memory.fail(edition_id)
        raise
