from pipeline.edition_slots import (
    EDITION_SLOTS,
    EDITION_TIMEZONE,
    get_edition_slots,
    is_valid_edition_time,
)


def test_edition_slots_are_canonical():
    assert EDITION_SLOTS == (
        "07:00",
        "13:00",
        "20:00",
    )


def test_edition_timezone_is_new_york():
    assert EDITION_TIMEZONE == "America/New_York"


def test_get_edition_slots_returns_all_slots():
    assert get_edition_slots() == (
        "07:00",
        "13:00",
        "20:00",
    )


def test_configured_edition_time_is_valid():
    assert is_valid_edition_time("07:00") is True
    assert is_valid_edition_time("13:00") is True
    assert is_valid_edition_time("20:00") is True


def test_unconfigured_edition_time_is_invalid():
    assert is_valid_edition_time("08:00") is False
    assert is_valid_edition_time("19:00") is False
    assert is_valid_edition_time("21:00") is False
