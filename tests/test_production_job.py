from datetime import datetime

import pytest

from pipeline.edition_memory import (
    COMPLETED,
    EditionMemory,
)
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
