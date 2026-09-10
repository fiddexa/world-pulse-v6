"""
AROUND THE MAIN v6 - Production Job

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
from pipeline.connector_config import get_connector_registry
from pipeline.source_connectors import (
    build_connectors,
    collect_from_connectors,
)
from pipeline.production_scheduler import run_scheduled_edition
from pipeline.edition_runner import run_edition
from pipeline.edition_counter import EditionCounter


def collect_production_articles(*, timeout=15):
    """
    Collect production news through the configured Source Connector Layer.

    Only explicitly enabled connectors participate.

    Connector failures are isolated by collect_from_connectors().
    """
    connector_registry = get_connector_registry()

    configured_feeds = get_feeds()

    feed_registry = {
        source: []
        for source in connector_registry
    }

    if isinstance(configured_feeds, (list, tuple)):
        for feed in configured_feeds:
            if not isinstance(feed, dict):
                continue

            source = str(
                feed.get("source") or ""
            ).strip().lower()

            if source in feed_registry:
                feed_registry[source].append(feed)

    connectors = build_connectors(
        feed_registry=feed_registry,
        connector_registry=connector_registry,
        collector=collect,
        timeout=timeout,
    )

    return collect_from_connectors(connectors)


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
            articles = collect_production_articles(
                timeout=timeout,
            )
        else:
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

def run_test_production_job(
    *,
    publication_date,
    edition_time,
    timeout=20,
    language="en",
    event_memory=None,
):
    """
    Manual production test.

    The edition date and time are supplied explicitly.
    No production slot resolver or automatic schedule is used.

    This mode is intended for controlled testing before
    automatic publication is enabled.
    """

    if not publication_date:
        raise ValueError(
            "publication_date is required"
        )

    if not edition_time:
        raise ValueError(
            "edition_time is required"
        )

    articles = collect_production_articles(
        timeout=timeout,
    )

    print(
        f"Collected production articles: {len(articles)}"
    )

    if event_memory is None:
        event_memory = EventMemory()

    edition = run_edition(
        articles,
        publication_date=publication_date,
        edition_time=edition_time,
        event_memory=event_memory,
        edition_memory=None,
        language=language,
        exclude_ignored=True,
    )

    if not isinstance(edition, dict):
        return {
            "status": "FAILED",
            "reason": "EDITION_NOT_CREATED",
        }

    edition_id = str(
        edition.get("edition_id") or ""
    ).strip()

    # Preserve the explicit publication date inside the edition
    # so downstream renderers can display it dynamically.
    edition["publication_date"] = str(
        publication_date
    )

    edition_year = int(
        str(publication_date)[:4]
    )

    counter = EditionCounter(
        "data/edition_counter.json"
    )

    edition_number = counter.allocate(
        edition_year,
        edition_id,
    )

    edition["edition_year"] = edition_number.year
    edition["edition_number"] = edition_number.number
    edition["edition_label"] = edition_number.label

    return {
        "status": "COMPLETED",
        "edition_id": edition_id,
        "edition_year": edition_number.year,
        "edition_number": edition_number.number,
        "edition_label": edition_number.label,
        "edition_date": str(publication_date),
        "edition_time": str(edition_time),
        "edition": edition,
    }
