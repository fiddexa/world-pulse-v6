from datetime import datetime, timezone

from pipeline.editorial_snapshot import (
    SNAPSHOT_ELIGIBLE,
    SNAPSHOT_EXCLUDED,
    SNAPSHOT_UNKNOWN,
    annotate_snapshot,
    filter_events_for_snapshot,
    first_known_at,
    is_snapshot_eligible,
    last_known_at,
    snapshot_status,
)


SNAPSHOT_0700 = datetime(
    2026,
    8,
    30,
    7,
    0,
    tzinfo=timezone.utc,
)

SNAPSHOT_1300 = datetime(
    2026,
    8,
    30,
    13,
    0,
    tzinfo=timezone.utc,
)


def event(*, first_seen_at=None, published_at=None):
    return {
        "articles": [
            {
                "title": "Test event",
                "published_at": published_at,
                "first_seen_at": first_seen_at,
            }
        ]
    }


def test_information_known_before_snapshot_is_eligible():
    item = event(
        first_seen_at="2026-08-30T06:50:00Z",
        published_at="2026-08-30T06:45:00Z",
    )

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_ELIGIBLE
    assert is_snapshot_eligible(item, SNAPSHOT_0700) is True


def test_information_known_after_snapshot_is_excluded():
    item = event(
        first_seen_at="2026-08-30T07:20:00Z",
        published_at="2026-08-30T07:20:00Z",
    )

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_EXCLUDED
    assert is_snapshot_eligible(item, SNAPSHOT_0700) is False


def test_late_information_is_eligible_for_later_edition():
    item = event(
        first_seen_at="2026-08-30T07:20:00Z",
        published_at="2026-08-30T07:20:00Z",
    )

    assert is_snapshot_eligible(item, SNAPSHOT_0700) is False
    assert is_snapshot_eligible(item, SNAPSHOT_1300) is True


def test_event_time_does_not_control_snapshot_eligibility():
    item = event(
        first_seen_at="2026-08-30T07:20:00Z",
        published_at="2026-08-30T07:20:00Z",
    )
    item["event_time"] = "2026-08-30T05:30:00Z"

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_EXCLUDED
    assert snapshot_status(item, SNAPSHOT_1300) == SNAPSHOT_ELIGIBLE


def test_event_level_first_seen_takes_precedence_over_article_times():
    item = {
        "first_seen_at": "2026-08-30T06:55:00Z",
        "articles": [
            {
                "published_at": "2026-08-30T07:20:00Z",
            }
        ],
    }

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_ELIGIBLE


def test_event_level_first_seen_can_exclude_despite_older_article_publication():
    item = {
        "first_seen_at": "2026-08-30T07:20:00Z",
        "articles": [
            {
                "published_at": "2026-08-30T06:00:00Z",
            }
        ],
    }

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_EXCLUDED


def test_published_at_is_compatibility_fallback():
    item = event(
        first_seen_at=None,
        published_at="2026-08-30T06:55:00Z",
    )

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_ELIGIBLE


def test_missing_availability_is_unknown():
    item = {"articles": [{"title": "No timestamp"}]}

    assert snapshot_status(item, SNAPSHOT_0700) == SNAPSHOT_UNKNOWN
    assert is_snapshot_eligible(item, SNAPSHOT_0700) is False


def test_first_and_last_known_times_use_first_seen_tier():
    item = {
        "articles": [
            {
                "first_seen_at": "2026-08-30T07:20:00Z",
                "published_at": "2026-08-30T07:15:00Z",
            },
            {
                "first_seen_at": "2026-08-30T08:10:00Z",
                "published_at": "2026-08-30T08:05:00Z",
            },
        ]
    }

    assert first_known_at(item) == datetime(
        2026, 8, 30, 7, 20, tzinfo=timezone.utc
    )
    assert last_known_at(item) == datetime(
        2026, 8, 30, 8, 10, tzinfo=timezone.utc
    )


def test_filter_events_for_snapshot_excludes_late_information():
    events = [
        event(first_seen_at="2026-08-30T06:50:00Z"),
        event(first_seen_at="2026-08-30T07:20:00Z"),
    ]

    result = filter_events_for_snapshot(events, SNAPSHOT_0700)

    assert len(result) == 1
    assert result[0]["articles"][0]["first_seen_at"] == (
        "2026-08-30T06:50:00Z"
    )


def test_filter_events_for_snapshot_excludes_unknown_by_default():
    events = [
        event(first_seen_at="2026-08-30T06:50:00Z"),
        {"articles": [{"title": "Unknown availability"}]},
    ]

    result = filter_events_for_snapshot(events, SNAPSHOT_0700)

    assert len(result) == 1


def test_filter_events_for_snapshot_can_include_unknown_for_compatibility():
    events = [
        event(first_seen_at="2026-08-30T06:50:00Z"),
        {"articles": [{"title": "Unknown availability"}]},
    ]

    result = filter_events_for_snapshot(
        events,
        SNAPSHOT_0700,
        include_unknown=True,
    )

    assert len(result) == 2


def test_annotate_snapshot_does_not_modify_original():
    item = event(
        first_seen_at="2026-08-30T06:50:00Z",
        published_at="2026-08-30T06:45:00Z",
    )
    before = dict(item)

    result = annotate_snapshot(item, SNAPSHOT_0700)

    assert item == before
    assert result["editorial_snapshot"]["status"] == SNAPSHOT_ELIGIBLE
    assert result["editorial_snapshot"]["editorial_time"] == (
        "2026-08-30T07:00:00+00:00"
    )


def test_naive_editorial_time_is_supported_as_utc():
    item = event(
        first_seen_at="2026-08-30T06:50:00Z",
    )

    assert snapshot_status(
        item,
        datetime(2026, 8, 30, 7, 0),
    ) == SNAPSHOT_ELIGIBLE
