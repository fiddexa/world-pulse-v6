from datetime import datetime, timezone

from pipeline.ranking import (
    editorial_level,
    editorial_score,
    freshness_score,
    is_breaking,
    rank_event,
    rank_events,
)


NOW = datetime(
    2026,
    1,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)


def event(
    intelligence=50,
    verification=50,
    published_at="2026-01-01T11:00:00+00:00",
    article_count=1,
):
    articles = [
        {
            "title": f"Report {i}",
            "source": f"Source {i}",
            "published_at": published_at,
        }
        for i in range(article_count)
    ]

    return {
        "articles": articles,
        "intelligence": {
            "score": intelligence,
        },
        "verification": {
            "verification_score": verification,
        },
    }


def test_fresh_event_gets_high_freshness():
    result = freshness_score(
        event(
            published_at="2026-01-01T11:30:00+00:00"
        ),
        NOW,
    )

    assert result == 100.0


def test_old_event_gets_low_freshness():
    result = freshness_score(
        event(
            published_at="2025-12-29T12:00:00+00:00"
        ),
        NOW,
    )

    assert result == 10.0


def test_unknown_time_is_neutral():
    result = freshness_score(
        event(published_at=None),
        NOW,
    )

    assert result == 50.0
def test_high_impact_recent_event_has_high_editorial_score():
    result = editorial_score(
        event(
            intelligence=95,
            verification=90,
            published_at="2026-01-01T11:30:00+00:00",
            article_count=4,
        ),
        NOW,
    )

    assert result >= 85.0


def test_editorial_score_is_not_same_as_intelligence():
    result = editorial_score(
        event(
            intelligence=80,
            verification=20,
            published_at="2025-12-31T12:00:00+00:00",
        ),
        NOW,
    )

    assert result != 80


def test_editorial_levels():
    assert editorial_level(90) == "FRONT_PAGE"
    assert editorial_level(75) == "TOP_STORY"
    assert editorial_level(60) == "IMPORTANT"
    assert editorial_level(45) == "STANDARD"
    assert editorial_level(20) == "LOW_PRIORITY"


def test_major_recent_event_is_breaking():
    result = is_breaking(
        event(
            intelligence=80,
            published_at="2026-01-01T11:30:00+00:00",
        ),
        NOW,
    )

    assert result is True


def test_old_event_is_not_breaking():
    result = is_breaking(
        event(
            intelligence=100,
            published_at="2025-12-30T12:00:00+00:00",
        ),
        NOW,
    )

    assert result is False


def test_rank_event_does_not_modify_original():
    original = event(
        intelligence=80,
        verification=70,
    )

    before = dict(original)

    result = rank_event(original, NOW)

    assert original == before
    assert "ranking" in result


def test_rank_events_orders_highest_first():
    events = [
        event(intelligence=30, verification=30),
        event(intelligence=95, verification=90),
        event(intelligence=60, verification=60),
    ]

    result = rank_events(events, NOW)

    scores = [
        item["ranking"]["editorial_score"]
        for item in result
    ]

    assert scores == sorted(scores, reverse=True)


def test_rank_events_preserves_tie_order():
    events = [
        event(intelligence=50, verification=50),
        event(intelligence=50, verification=50),
    ]

    result = rank_events(events, NOW)

    assert result[0]["articles"][0]["title"] == "Report 0"
    assert result[1]["articles"][0]["title"] == "Report 0"


def test_invalid_input_is_safe():
    assert rank_events(None, NOW) == []
    assert rank_event(None, NOW) == {}
    assert editorial_score(None, NOW) == 0.0
