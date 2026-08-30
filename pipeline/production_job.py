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
    production job
        ↓
    feed configuration
        ↓
    collect news
        ↓
    production scheduler
        ↓
    edition runner
        ↓
    edition result
"""

from datetime import datetime
from typing import Any

from pipeline.collector import collect
from pipeline.edition_memory import EditionMemory
from pipeline.event_memory import EventMemory
from pipeline.feed_config import get_feeds
from pipeline.production_scheduler import run_scheduled_edition


def run_production_job(
    articles: Any = None,
    current_time: datetime = None,
    *,
    feeds=None,
    timeout: int = 15,
    edition_memory=None,
    event_memory=None,
    language: str = "en",
) -> dict:
    """
    Execute one production edition job.

    Three input modes are supported.

    1. Supplied articles

        run_production_job(
            articles,
            current_time,
        )

    This mode is useful for tests, rehearsals and controlled
    execution.

    2. Explicit feeds

        run_production_job(
            current_time=current_time,
            feeds=feeds,
        )

    In this mode the job collects news from the supplied
    RSS/Atom feeds.

    3. Production feed registry

        run_production_job(
            current_time=current_time,
        )

    In this mode the job automatically loads feeds from
    pipeline.feed_config.get_feeds().

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

    if articles is not None and feeds is not None:
        raise ValueError(
            "articles and feeds cannot be supplied together"
        )

    if articles is None:
        if feeds is None:
            feeds = get_feeds()

        articles = collect(
            feeds,
            timeout=timeout,
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
