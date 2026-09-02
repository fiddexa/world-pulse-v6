from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.edition_slot_resolver import (
    resolve_edition_slot,
)


def test_before_first_slot_uses_previous_day_evening():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            6,
            59,
        )
    )

    assert result == {
        "edition_date": "2026-08-29",
        "edition_time": "20:00",
        "edition_id": (
            "AROUND-THE-MAIN-EN-2026-08-29-2000"
        ),
    }


def test_first_slot_starts_at_0700():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            7,
            0,
        )
    )

    assert result["edition_date"] == "2026-08-30"
    assert result["edition_time"] == "07:00"
    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-0700"
    )


def test_between_morning_and_afternoon():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            12,
            59,
        )
    )

    assert result["edition_time"] == "07:00"


def test_afternoon_slot_starts_at_1300():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            13,
            0,
        )
    )

    assert result["edition_time"] == "13:00"
    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )


def test_between_afternoon_and_evening():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            19,
            59,
        )
    )

    assert result["edition_time"] == "13:00"


def test_evening_slot_starts_at_2000():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            20,
            0,
        )
    )

    assert result["edition_time"] == "20:00"
    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-2000"
    )


def test_late_evening_stays_on_same_date():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            23,
            59,
        )
    )

    assert result["edition_date"] == "2026-08-30"
    assert result["edition_time"] == "20:00"


def test_utc_datetime_is_converted_to_new_york():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            3,
            0,
            tzinfo=ZoneInfo("UTC"),
        )
    )

    assert result["edition_date"] == "2026-08-29"
    assert result["edition_time"] == "20:00"


def test_custom_language_is_used():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            13,
            0,
        ),
        language="fr",
    )

    assert result["edition_id"] == (
        "AROUND-THE-MAIN-FR-2026-08-30-1300"
    )


def test_naive_datetime_is_interpreted_as_new_york():
    result = resolve_edition_slot(
        datetime(
            2026,
            8,
            30,
            13,
            0,
        )
    )

    assert result["edition_date"] == "2026-08-30"
    assert result["edition_time"] == "13:00"
