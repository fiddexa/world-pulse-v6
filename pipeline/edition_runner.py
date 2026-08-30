"""
WORLD PULSE v6 - Edition Runner

Runs one deterministic WORLD PULSE edition.

This layer:
- receives the edition date and time explicitly;
- processes the supplied articles;
- builds the edition;
- records event usage in persistent Event Memory.

It does not schedule future runs.
It does not publish externally.
It does not perform Telegram delivery.
"""

from pipeline.app import build_edition_from_articles
from pipeline.event_memory import EventMemory


def run_edition(
    articles,
    publication_date,
    edition_time,
    *,
    event_memory=None,
):
    """
    Build one WORLD PULSE edition.

    Publication date and edition time are explicit so that a future
    scheduler can control the three daily edition slots.

    Event Memory is optional for compatibility and testing.
    """

    if event_memory is None:
        event_memory = EventMemory()

    return build_edition_from_articles(
        articles,
        publication_date=publication_date,
        edition_time=edition_time,
        event_memory=event_memory,
    )
