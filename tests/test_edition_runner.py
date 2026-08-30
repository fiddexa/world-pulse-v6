from datetime import datetime

import pytest

from pipeline.edition_memory import (
    COMPLETED,
    FAILED,
    EditionMemory,
)
from pipeline.edition_runner import run_edition
from pipeline.event_memory import EventMemory


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


def test_run_edition_builds_stable_edition():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "07:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    assert edition["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-0700"
    )

    assert edition["event_count"] == 1

    assert edition_memory.status(
        edition["edition_id"]
    ) == COMPLETED

    memory.close()
    edition_memory.close()


def test_run_edition_records_event_in_memory():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "13:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    event = edition["top_story"]

    if event is None:
        event = (
            edition["main_stories"]
            + edition["briefs"]
        )[0]

    assert memory.has_seen(event) is True

    assert memory.edition_history(event) == [
        "WORLD-PULSE-EN-2026-08-30-1300"
    ]

    memory.close()
    edition_memory.close()


def test_run_edition_uses_supplied_memory():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "20:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    event = edition["top_story"]

    if event is None:
        event = (
            edition["main_stories"]
            + edition["briefs"]
        )[0]

    stored = memory.get(event)

    assert stored is not None

    assert stored["last_edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-2000"
    )

    memory.close()
    edition_memory.close()


def test_run_edition_resolves_slot_from_current_time():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    edition = run_edition(
        articles(),
        current_time=datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        event_memory=memory,
        edition_memory=edition_memory,
    )

    assert edition["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    assert edition_memory.status(
        edition["edition_id"]
    ) == COMPLETED

    memory.close()
    edition_memory.close()


def test_run_edition_resolves_previous_day_before_first_slot():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    edition = run_edition(
        articles(),
        current_time=datetime(
            2026,
            8,
            30,
            6,
            59,
        ),
        event_memory=memory,
        edition_memory=edition_memory,
    )

    assert edition["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-29-2000"
    )

    assert edition_memory.status(
        edition["edition_id"]
    ) == COMPLETED

    memory.close()
    edition_memory.close()


def test_run_edition_rejects_mixed_resolution_modes():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    with pytest.raises(ValueError):
        run_edition(
            articles(),
            "2026-08-30",
            "13:00",
            current_time=datetime(
                2026,
                8,
                30,
                13,
                45,
            ),
            event_memory=memory,
            edition_memory=edition_memory,
        )

    memory.close()
    edition_memory.close()


def test_run_edition_requires_edition_identity():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    with pytest.raises(ValueError):
        run_edition(
            articles(),
            event_memory=memory,
            edition_memory=edition_memory,
        )

    memory.close()
    edition_memory.close()


def test_run_edition_skips_duplicate_edition():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    first = run_edition(
        articles(),
        "2026-08-30",
        "13:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    second = run_edition(
        articles(),
        "2026-08-30",
        "13:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    assert first is not None
    assert second is None

    assert edition_memory.status(
        "WORLD-PULSE-EN-2026-08-30-1300"
    ) == COMPLETED

    memory.close()
    edition_memory.close()


def test_different_edition_slots_are_independent():
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    morning = run_edition(
        articles(),
        "2026-08-30",
        "07:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    afternoon = run_edition(
        articles(),
        "2026-08-30",
        "13:00",
        event_memory=memory,
        edition_memory=edition_memory,
    )

    assert morning is not None
    assert afternoon is not None

    assert edition_memory.status(
        "WORLD-PULSE-EN-2026-08-30-0700"
    ) == COMPLETED

    assert edition_memory.status(
        "WORLD-PULSE-EN-2026-08-30-1300"
    ) == COMPLETED

    memory.close()
    edition_memory.close()


def test_failed_edition_is_recorded(monkeypatch):
    memory = EventMemory(":memory:")
    edition_memory = EditionMemory(":memory:")

    def broken_build(*args, **kwargs):
        raise RuntimeError(
            "simulated edition build failure"
        )

    monkeypatch.setattr(
        "pipeline.edition_runner.build_edition_from_articles",
        broken_build,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated edition build failure",
    ):
        run_edition(
            articles(),
            "2026-08-30",
            "20:00",
            event_memory=memory,
            edition_memory=edition_memory,
        )

    assert edition_memory.status(
        "WORLD-PULSE-EN-2026-08-30-2000"
    ) == FAILED

    memory.close()
    edition_memory.close()
