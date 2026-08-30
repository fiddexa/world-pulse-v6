"""
WORLD PULSE v6 - Production Job

Single production entrypoint for one autonomous edition execution.

This module is intentionally stateless between invocations.

A hosted production scheduler is responsible for invoking this job.
The job itself does not:
- wait for scheduled times;
- run an infinite loop;
- create cron jobs;
- depend on Codespace;
- publish directly.

Execution flow:

    current time
        ↓
    production scheduler
        ↓
    edition runner
        ↓
    edition result
"""

from datetime import datetime
from typing import Any

from pipeline.edition_memory import EditionMemory
from pipeline.event_memory import EventMemory
from pipeline.production_scheduler import run_scheduled_edition


def run_production_job(
    articles: Any,
    current_time: datetime,
    *,
    edition_memory=None,
    event_memory=None,
    language: str = "en",
) -> dict:
    """
    Execute one production edition job.

    The current time is supplied by the external execution
    environment. The job does not determine when it should run.

    Persistent Edition Memory and Event Memory may be injected
    by the production environment. When omitted, their default
    persistent SQLite stores are used.

    Returns the structured result produced by the production
    scheduler.
    """

    if not isinstance(current_time, datetime):
        raise ValueError(
            "current_time must be a datetime"
        )

    if edition_memory is None:
        edition_memory = EditionMemory()

    if event_memory is None:
        event_memory = EventMemory()

    return run_scheduled_edition(
        articles,
        current_time,
        edition_memory=edition_memory,
        event_memory=event_memory,
        language=language,
    )
