"""
AROUND THE MAIN v6 - Production Scheduler

Deterministic scheduler core for autonomous edition execution.

This module:
- resolves the active AROUND THE MAIN edition slot;
- builds the stable Edition ID;
- prevents duplicate execution using EditionMemory;
- launches the Edition Runner;
- records final scheduler execution state.

It does not:
- wait for time;
- create its own infinite loop;
- publish externally;
- collect news;
- replace the Edition Runner.

A hosted production environment is responsible for invoking this
scheduler at the appropriate times.
"""

from datetime import datetime
from typing import Any

from pipeline.edition_memory import (
    COMPLETED,
    FAILED,
    RUNNING,
    EditionMemory,
)
from pipeline.edition_runner import run_edition
from pipeline.edition_slot_resolver import resolve_edition_slot


SKIPPED = "SKIPPED"
STARTED = "STARTED"
COMPLETED_RESULT = "COMPLETED"
FAILED_RESULT = "FAILED"


def get_scheduled_edition(
    current_time: datetime,
    *,
    language: str = "en",
) -> dict:
    """
    Resolve the edition slot for the supplied moment.

    Returns the canonical edition date, time and Edition ID.
    """

    return resolve_edition_slot(
        current_time,
        language=language,
    )


def run_scheduled_edition(
    articles: Any,
    current_time: datetime,
    *,
    edition_memory=None,
    event_memory=None,
    language: str = "en",
) -> dict:
    """
    Run the edition corresponding to current_time.

    The scheduler owns the edition-level execution reservation.

    Existing states behave as follows:

    - no state       -> start execution;
    - RUNNING        -> skipped;
    - COMPLETED      -> skipped;
    - FAILED         -> skipped.

    A failed execution is persisted as FAILED and the original
    exception is re-raised so callers can observe the failure.
    """

    resolved = get_scheduled_edition(
        current_time,
        language=language,
    )

    edition_id = resolved["edition_id"]

    if edition_memory is None:
        edition_memory = EditionMemory()

    # Atomically reserve this edition.
    if not edition_memory.start(edition_id):
        return {
            "status": SKIPPED,
            "edition_id": edition_id,
            "edition_date": resolved["edition_date"],
            "edition_time": resolved["edition_time"],
            "previous_status": edition_memory.status(
                edition_id
            ),
        }

    try:
        # The scheduler already owns EditionMemory for this run.
        # Do not pass it to the runner, otherwise the runner would
        # attempt to start the same Edition ID a second time.
        edition = run_edition(
            articles,
            publication_date=resolved["edition_date"],
            edition_time=resolved["edition_time"],
            event_memory=event_memory,
            edition_memory=None,
            language=language,
            exclude_ignored=True
        )

        if edition is None:
            edition_memory.fail(edition_id)

            return {
                "status": FAILED_RESULT,
                "edition_id": edition_id,
                "edition_date": resolved["edition_date"],
                "edition_time": resolved["edition_time"],
            }

        edition_memory.complete(edition_id)

        return {
            "status": COMPLETED_RESULT,
            "edition_id": edition_id,
            "edition_date": resolved["edition_date"],
            "edition_time": resolved["edition_time"],
            "edition": edition,
        }

    except Exception:
        edition_memory.fail(edition_id)
        raise
