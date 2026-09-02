from datetime import datetime

import pytest

from pipeline.edition_memory import (
    COMPLETED,
    FAILED,
    RUNNING,
    EditionMemory,
)
from pipeline.event_memory import EventMemory
from pipeline.production_scheduler import (
    COMPLETED_RESULT,
    FAILED_RESULT,
    SKIPPED,
    run_scheduled_edition,
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


def test_scheduler_runs_correct_slot():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_scheduled_edition(
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
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    assert result["edition_time"] == "13:00"

    assert edition_memory.status(
        result["edition_id"]
    ) == COMPLETED

    edition_memory.close()
    event_memory.close()


def test_scheduler_prevents_duplicate_execution():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    current_time = datetime(
        2026,
        8,
        30,
        13,
        45,
    )

    first = run_scheduled_edition(
        articles(),
        current_time,
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    second = run_scheduled_edition(
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


def test_scheduler_marks_running_before_execution():
    edition_memory = EditionMemory(":memory:")

    edition_id = (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    assert edition_memory.start(edition_id) is True

    result = run_scheduled_edition(
        articles(),
        datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        edition_memory=edition_memory,
    )

    assert result["status"] == SKIPPED
    assert result["previous_status"] == RUNNING

    edition_memory.close()


def test_scheduler_handles_previous_day_slot():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_scheduled_edition(
        articles(),
        datetime(
            2026,
            8,
            30,
            6,
            59,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert result["status"] == COMPLETED_RESULT

    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-29-2000"
    )

    edition_memory.close()
    event_memory.close()


def test_scheduler_supports_all_three_slots():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    morning = run_scheduled_edition(
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

    afternoon = run_scheduled_edition(
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

    evening = run_scheduled_edition(
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

    assert morning["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-0700"
    )

    assert afternoon["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    assert evening["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-2000"
    )

    edition_memory.close()
    event_memory.close()


def test_failed_scheduler_execution_is_recorded(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    def broken_runner(*args, **kwargs):
        raise RuntimeError(
            "simulated scheduler failure"
        )

    monkeypatch.setattr(
        "pipeline.production_scheduler.run_edition",
        broken_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated scheduler failure",
    ):
        run_scheduled_edition(
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

    assert edition_memory.status(
        "AROUND-THE-MAIN-EN-2026-08-30-2000"
    ) == FAILED

    edition_memory.close()
    event_memory.close()


def test_failed_edition_does_not_report_success(
    monkeypatch,
):
    edition_memory = EditionMemory(":memory:")

    def failed_runner(*args, **kwargs):
        raise RuntimeError("failure")

    monkeypatch.setattr(
        "pipeline.production_scheduler.run_edition",
        failed_runner,
    )

    with pytest.raises(RuntimeError):
        run_scheduled_edition(
            articles(),
            datetime(
                2026,
                8,
                30,
                20,
                0,
            ),
            edition_memory=edition_memory,
        )

    assert edition_memory.status(
        "AROUND-THE-MAIN-EN-2026-08-30-2000"
    ) == FAILED

    edition_memory.close()


def test_scheduler_uses_custom_language():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")

    result = run_scheduled_edition(
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
        language="fr",
    )

    assert result["edition_id"] == (
        "AROUND-THE-MAIN-FR-2026-08-30-1300"
    )

    edition_memory.close()
    event_memory.close()
