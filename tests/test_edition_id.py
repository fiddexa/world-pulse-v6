from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from pipeline.edition_id import (
    DEFAULT_LANGUAGE,
    DEFAULT_TIMEZONE,
    build_edition_id,
)


def test_build_edition_id():
    result = build_edition_id(
        date(2026, 8, 30),
        "07:00",
    )

    assert result == (
        "AROUND-THE-MAIN-EN-2026-08-30-0700"
    )


def test_edition_id_is_deterministic():
    first = build_edition_id(
        "2026-08-30",
        "13:00",
    )

    second = build_edition_id(
        "2026-08-30",
        "13:00",
    )

    assert first == second


def test_different_times_produce_different_ids():
    morning = build_edition_id(
        "2026-08-30",
        "07:00",
    )

    evening = build_edition_id(
        "2026-08-30",
        "20:00",
    )

    assert morning != evening


def test_different_dates_produce_different_ids():
    first = build_edition_id(
        "2026-08-30",
        "07:00",
    )

    second = build_edition_id(
        "2026-08-31",
        "07:00",
    )

    assert first != second


def test_language_is_part_of_id():
    result = build_edition_id(
        "2026-08-30",
        "07:00",
        language="en",
    )

    assert "-EN-" in result


def test_timezone_is_validated():
    with pytest.raises(ValueError):
        build_edition_id(
            "2026-08-30",
            "07:00",
            timezone="Invalid/Timezone",
        )


def test_invalid_time_is_rejected():
    with pytest.raises(ValueError):
        build_edition_id(
            "2026-08-30",
            "25:00",
        )


def test_invalid_date_is_rejected():
    with pytest.raises(ValueError):
        build_edition_id(
            "not-a-date",
            "07:00",
        )


def test_datetime_is_converted_to_requested_timezone():
    value = datetime(
        2026,
        8,
        30,
        23,
        30,
        tzinfo=ZoneInfo("UTC"),
    )

    result = build_edition_id(
        value,
        "07:00",
        timezone=DEFAULT_TIMEZONE,
    )

    assert result.startswith(
        "AROUND-THE-MAIN-EN-2026-08-30-"
    )


def test_default_language_is_english():
    assert DEFAULT_LANGUAGE == "en"


def test_default_timezone_is_new_york():
    assert DEFAULT_TIMEZONE == "America/New_York"
