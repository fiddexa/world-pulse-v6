from pathlib import Path

import pytest

from pipeline.edition_counter import EditionCounter


def test_first_edition_starts_at_0001(tmp_path: Path):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    result = counter.allocate(
        2026,
        "2026-09-01-0700",
    )

    assert result.number == 1
    assert result.label == "EDITION 0001"


def test_counter_increments_for_new_edition(tmp_path: Path):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    first = counter.allocate(
        2026,
        "2026-09-01-0700",
    )

    second = counter.allocate(
        2026,
        "2026-09-01-1200",
    )

    third = counter.allocate(
        2026,
        "2026-09-01-2000",
    )

    assert first.number == 1
    assert second.number == 2
    assert third.number == 3

    assert first.label == "EDITION 0001"
    assert second.label == "EDITION 0002"
    assert third.label == "EDITION 0003"


def test_same_edition_slot_does_not_increment(
    tmp_path: Path,
):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    first = counter.allocate(
        2026,
        "2026-09-01-0700",
    )

    repeated = counter.allocate(
        2026,
        "2026-09-01-0700",
    )

    assert first.number == 1
    assert repeated.number == 1


def test_counter_persists_after_restart(
    tmp_path: Path,
):
    path = tmp_path / "counter.json"

    counter_a = EditionCounter(path)

    first = counter_a.allocate(
        2026,
        "2026-09-01-0700",
    )

    second = counter_a.allocate(
        2026,
        "2026-09-01-1200",
    )

    # Simulate a new process.
    counter_b = EditionCounter(path)

    repeated = counter_b.allocate(
        2026,
        "2026-09-01-0700",
    )

    third = counter_b.allocate(
        2026,
        "2026-09-01-2000",
    )

    assert first.number == 1
    assert second.number == 2
    assert repeated.number == 1
    assert third.number == 3


def test_new_year_starts_at_0001(
    tmp_path: Path,
):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    old_year = counter.allocate(
        2026,
        "2026-12-31-2000",
    )

    new_year = counter.allocate(
        2027,
        "2027-01-01-0700",
    )

    next_new_year = counter.allocate(
        2027,
        "2027-01-01-1200",
    )

    assert old_year.number == 1
    assert old_year.label == "EDITION 0001"

    assert new_year.number == 1
    assert new_year.label == "EDITION 0001"

    assert next_new_year.number == 2
    assert next_new_year.label == "EDITION 0002"


def test_get_does_not_allocate(
    tmp_path: Path,
):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    assert counter.get(
        2026,
        "2026-09-01-0700",
    ) is None

    first = counter.allocate(
        2026,
        "2026-09-01-0700",
    )

    result = counter.get(
        2026,
        "2026-09-01-0700",
    )

    assert result is not None
    assert result.number == first.number


def test_counter_rejects_empty_slot(
    tmp_path: Path,
):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    with pytest.raises(ValueError):
        counter.allocate(
            2026,
            "",
        )


def test_counter_stops_after_9999(
    tmp_path: Path,
):
    counter = EditionCounter(
        tmp_path / "counter.json"
    )

    for number in range(1, 10000):
        counter.allocate(
            2026,
            f"slot-{number}",
        )

    assert counter.allocate(
        2026,
        "slot-9999",
    ).number == 9999

    with pytest.raises(RuntimeError):
        counter.allocate(
            2026,
            "slot-10000",
        )
