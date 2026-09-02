"""
AROUND THE MAIN v6 - Edition Runner

Runs one deterministic AROUND THE MAIN edition.

This layer:
- receives the edition date and time explicitly, or resolves them
  from a supplied current time;
- processes the supplied articles;
- builds the edition;
- records event usage in persistent Event Memory;
- optionally protects execution with Edition Memory.

The production scheduler may reserve an edition before calling this
runner. In that case the runner must reuse the existing RUNNING state
instead of attempting to start the edition again.

It does not schedule future runs.
It does not publish externally.
It does not perform Telegram delivery.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.app import build_edition_from_articles
from pipeline.edition_id import (
    DEFAULT_TIMEZONE,
    build_edition_id,
)
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
    exclude_ignored=False,
):
    """
    Build one AROUND THE MAIN edition.

    Two identity modes are supported.

    Explicit mode:
        publication_date + edition_time

    Resolver mode:
        current_time

    Edition Memory behavior:

    - If no Edition Memory is supplied, no edition-level
      idempotency is applied by this runner.
    - If Edition Memory is supplied and the edition has no state,
      the runner starts it.
    - If Edition Memory already contains RUNNING for this edition,
      the runner assumes that an outer scheduler owns the reservation.
    - If Edition Memory contains COMPLETED or FAILED, execution
      is rejected by returning None.

    This allows production_scheduler to reserve the edition before
    invoking the runner while preserving direct runner compatibility.
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

    editorial_time = datetime.fromisoformat(
        f"{publication_date}T{edition_time}"
    ).replace(
        tzinfo=ZoneInfo(DEFAULT_TIMEZONE)
    )

    if edition_memory is None:
        return build_edition_from_articles(
            articles,
            publication_date=publication_date,
            edition_time=edition_time,
            event_memory=event_memory,
            editorial_time=editorial_time,
            exclude_ignored=exclude_ignored,
        )

    edition_id = build_edition_id(
        publication_date,
        edition_time,
        language=language,
    )

    existing_status = edition_memory.status(
        edition_id
    )

    if existing_status is None:
        if not edition_memory.start(edition_id):
            return None

        owns_execution = True

    elif existing_status == RUNNING:
        # An outer scheduler may have already reserved this edition.
        # The runner is allowed to continue that execution.
        owns_execution = False

    else:
        # COMPLETED or FAILED editions must not be executed again.
        return None

    try:
        edition = build_edition_from_articles(
            articles,
            publication_date=publication_date,
            edition_time=edition_time,
            event_memory=event_memory,
            editorial_time=editorial_time,
            exclude_ignored=exclude_ignored,
        )

        if owns_execution:
            edition_memory.complete(edition_id)

        return edition

    except Exception:
        if owns_execution:
            edition_memory.fail(edition_id)

        raise
