from datetime import datetime

import pytest

from pipeline.edition_memory import (
    COMPLETED,
    EditionMemory,
)
from pipeline.feed_config import get_feeds
from pipeline.event_memory import EventMemory
from pipeline.production_job import run_production_job
from pipeline.production_scheduler import (
    COMPLETED_RESULT,
    SKIPPED,
)


def articles():
    return [
        {
            "title": "Major earthquake strikes Nepal",
            "summary": "A powerful earthquake hits Nepal.",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
        {
            "title": "Strong earthquake hits Nepal",
            "summary": "The earthquake causes widespread damage.",
            "published_at": "2026-08-28T10:20:00Z",
            "source": "BBC",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
    ]


def test_production_job_runs_one_edition():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT

    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    assert result["edition_time"] == "13:00"

    assert edition_memory.status(
        result["edition_id"]
    ) == COMPLETED

    edition_memory.close()
    event_memory.close()


def test_production_job_is_idempotent():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    current_time = datetime(
        2026,
        8,
        30,
        13,
        45,
    )

    first = run_production_job(
        articles(),
        current_time,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    second = run_production_job(
        articles(),
        current_time,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert first["status"] == COMPLETED_RESULT
    assert second["status"] == SKIPPED

    assert second["previous_status"] == COMPLETED

    edition_memory.close()
    event_memory.close()


def test_production_job_supports_morning_slot():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            7,
            0,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-0700"
    )

    edition_memory.close()
    event_memory.close()


def test_production_job_supports_evening_slot():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            20,
            0,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-2000"
    )

    edition_memory.close()
    event_memory.close()


def test_production_job_uses_injected_memory():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            13,
            0,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT

    assert edition_memory.exists(
        result["edition_id"]
    ) is True

    edition_memory.close()
    event_memory.close()


def test_production_job_collects_from_feeds(monkeypatch):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    collected = articles()

    def fake_collect(feeds, timeout=15):
        assert feeds == [
            {
                "url": "https://example.com/feed.xml",
                "source": "Example",
            }
        ]
        assert timeout == 30

        return collected

    monkeypatch.setattr(
        "pipeline.production_job.collect",
        fake_collect,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        feeds=[
            {
                "url": "https://example.com/feed.xml",
                "source": "Example",
            }
        ],
        timeout=30,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT
    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    edition_memory.close()
    event_memory.close()


def test_production_job_rejects_articles_and_feeds_together():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    with pytest.raises(
        ValueError,
        match="articles and feeds cannot be supplied together",
    ):
        run_production_job(
            articles(),
            datetime(
                2026,
                8,
                30,
                13,
                0,
            ),
            feeds=[
                "https://example.com/feed.xml"
            ],
            edition_memory=edition_memory,
            event_memory=event_memory,
        )

    edition_memory.close()
    event_memory.close()


def test_production_job_uses_source_connectors_when_feeds_not_supplied(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    collected_articles = articles()
    calls = []

    def fake_collect_production_articles(timeout=15):
        calls.append(timeout)
        return collected_articles

    monkeypatch.setattr(
        "pipeline.production_job.collect_production_articles",
        fake_collect_production_articles,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        timeout=12,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT
    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )
    assert calls == [12]

    edition_memory.close()
    event_memory.close()


def test_production_job_rejects_invalid_current_time():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    with pytest.raises(
        ValueError,
        match="current_time must be a datetime",
    ):
        run_production_job(
            articles(),
            "2026-08-30T13:00:00",
            edition_memory=edition_memory,
            event_memory=event_memory,
        )

    edition_memory.close()
    event_memory.close()

def test_production_job_uses_configured_feeds(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    configured_feeds = [
        {
            "url": "https://example.com/feed.xml",
            "source": "Test Source",
            "type": "rss",
            "requires_auth": False,
        }
    ]

    collected_articles = articles()

    monkeypatch.setattr(
        "pipeline.production_job.get_feeds",
        lambda: configured_feeds,
    )

    def fake_collect(
        feeds,
        timeout=15,
    ):
        assert feeds == configured_feeds
        assert timeout == 9

        return collected_articles

    monkeypatch.setattr(
        "pipeline.production_job.collect",
        fake_collect,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        timeout=9,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT

    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    edition_memory.close()
    event_memory.close()


def test_explicit_feeds_override_configured_feeds(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    configured_feeds = [
        {
            "url": "https://example.com/configured.xml",
            "source": "Configured",
        }
    ]

    explicit_feeds = [
        {
            "url": "https://example.com/explicit.xml",
            "source": "Explicit",
        }
    ]

    monkeypatch.setattr(
        "pipeline.production_job.get_feeds",
        lambda: configured_feeds,
    )

    calls = []

    def fake_collect(
        feeds,
        timeout=15,
    ):
        calls.append(feeds)

        return articles()

    monkeypatch.setattr(
        "pipeline.production_job.collect",
        fake_collect,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        feeds=explicit_feeds,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT

    assert calls == [
        explicit_feeds
    ]

    edition_memory.close()
    event_memory.close()


def test_production_job_can_run_with_empty_connector_result(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    calls = []

    def fake_collect_production_articles(timeout=15):
        calls.append(timeout)
        return []

    monkeypatch.setattr(
        "pipeline.production_job.collect_production_articles",
        fake_collect_production_articles,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert calls == [15]

    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    edition_memory.close()
    event_memory.close()


def test_editorial_snapshot_time_changes_ranking():
    from datetime import datetime

    from pipeline.ranking import rank_events

    event = {
        "articles": [
            {
                "title": "Major earthquake",
                "published_at": "2026-08-30T05:00:00Z",
            }
        ],
        "intelligence": {
            "score": 70.0,
        },
        "verification": {
            "verification_score": 50.0,
        },
    }

    morning = rank_events(
        [event],
        now=datetime(2026, 8, 30, 7, 0),
    )[0]

    afternoon = rank_events(
        [event],
        now=datetime(2026, 8, 30, 13, 0),
    )[0]

    evening = rank_events(
        [event],
        now=datetime(2026, 8, 30, 20, 0),
    )[0]

    assert (
        morning["ranking"]["freshness_score"]
        > afternoon["ranking"]["freshness_score"]
    )

    assert (
        afternoon["ranking"]["freshness_score"]
        > evening["ranking"]["freshness_score"]
    )


def test_production_job_uses_source_connector_layer(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    collected_articles = articles()
    calls = []

    def fake_collect_production_articles(timeout=15):
        calls.append(timeout)
        return collected_articles

    monkeypatch.setattr(
        "pipeline.production_job.collect_production_articles",
        fake_collect_production_articles,
    )

    result = run_production_job(
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        timeout=21,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT
    assert calls == [21]

    edition_memory.close()
    event_memory.close()
