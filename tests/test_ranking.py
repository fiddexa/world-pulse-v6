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


def test_high_intelligence_single_source_can_still_rank_important():
    event = {
        "articles": [
            {
                "title": "Four children killed in Gaza",
                "published_at": "2026-08-31T12:00:00Z",
            }
        ],
        "intelligence": {
            "score": 47.0,
            "level": "MEDIUM",
        },
        "verification": {
            "verification_score": 42.0,
            "verification_level": "SINGLE_SOURCE",
        },
    }

    from datetime import datetime, timezone

    score = editorial_score(
        event,
        datetime(
            2026,
            8,
            31,
            13,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert score >= 55.0


def test_large_humanitarian_population_gets_important_priority():
    event = {
        "articles": [
            {
                "title": "One million children face deadly malnutrition",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["health", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 1,
                        "multiplier": 1_000_000,
                        "raw": "one million",
                        "context": "children",
                    }
                ],
            }
        ],
        "intelligence": {
            "score": 60.0,
            "level": "HIGH",
        },
        "verification": {
            "verification_score": 42.0,
            "verification_level": "SINGLE_SOURCE",
        },
    }

    score = editorial_score(
        event,
        NOW,
    )

    assert score >= 55.0


def test_mass_humanitarian_scale_beats_generic_background_event():
    humanitarian = {
        "articles": [
            {
                "title": "Millions of children face severe hunger",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["health", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 3.7,
                        "multiplier": 1_000_000,
                        "raw": "3.7 million",
                        "context": "children",
                    }
                ],
            }
        ],
        "intelligence": {
            "score": 60.0,
        },
        "verification": {
            "verification_score": 42.0,
        },
    }

    background = {
        "articles": [
            {
                "title": "Land degradation threatens billions of livelihoods",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["environmental"],
                "scale_numbers": [
                    {
                        "value": 3,
                        "multiplier": 1_000_000_000,
                        "raw": "3 billion",
                        "context": "livelihoods",
                    }
                ],
            }
        ],
        "intelligence": {
            "score": 60.0,
        },
        "verification": {
            "verification_score": 42.0,
        },
    }

    humanitarian_score = editorial_score(
        humanitarian,
        NOW,
    )

    background_score = editorial_score(
        background,
        NOW,
    )

    assert humanitarian_score > background_score


def test_recent_major_casualty_event_gets_high_priority():
    event = {
        "articles": [
            {
                "title": "Four children killed in separate attacks",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["attack", "casualty"],
                "casualty_numbers": ["4"],
            }
        ],
        "intelligence": {
            "score": 47.0,
        },
        "verification": {
            "verification_score": 42.0,
        },
    }

    score = editorial_score(
        event,
        NOW,
    )

    assert score >= 50.0


def test_direct_casualty_event_outranks_background_scale():
    casualty_event = {
        "articles": [
            {
                "title": "Four children killed in separate attacks",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["attack", "casualty"],
                "casualty_numbers": ["4"],
            }
        ],
        "intelligence": {"score": 47.0},
        "verification": {"verification_score": 42.0},
    }

    background_event = {
        "articles": [
            {
                "title": "Billions of livelihoods threatened by land degradation",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["environmental"],
                "scale_numbers": [
                    {
                        "value": 3,
                        "multiplier": 1_000_000_000,
                        "raw": "3 billion",
                        "context": "livelihoods",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    assert editorial_score(
        casualty_event,
        NOW,
    ) > editorial_score(
        background_event,
        NOW,
    )


def test_major_humanitarian_event_outranks_background_event():
    humanitarian = {
        "articles": [
            {
                "title": "Millions of children face severe malnutrition",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["health", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 3.7,
                        "multiplier": 1_000_000,
                        "raw": "3.7 million",
                        "context": "children",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    background = {
        "articles": [
            {
                "title": "Billions of livelihoods threatened by land degradation",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["environmental"],
                "scale_numbers": [
                    {
                        "value": 3,
                        "multiplier": 1_000_000_000,
                        "raw": "3 billion",
                        "context": "livelihoods",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    assert editorial_score(
        humanitarian,
        NOW,
    ) > editorial_score(
        background,
        NOW,
    )


def test_direct_humanitarian_harm_gets_bonus_over_livelihood_scale():
    humanitarian = {
        "articles": [
            {
                "title": "3.7 million children face severe malnutrition",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["health", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 3.7,
                        "multiplier": 1_000_000,
                        "raw": "3.7 million",
                        "context": "children",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    livelihoods = {
        "articles": [
            {
                "title": "3 billion livelihoods threatened by land degradation",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["environmental"],
                "scale_numbers": [
                    {
                        "value": 3,
                        "multiplier": 1_000_000_000,
                        "raw": "3 billion",
                        "context": "livelihoods",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    assert editorial_score(
        humanitarian,
        NOW,
    ) > editorial_score(
        livelihoods,
        NOW,
    )


def test_children_hunger_scale_is_high_priority():
    event = {
        "articles": [
            {
                "title": "One million children face deadly malnutrition",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["health", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 1,
                        "multiplier": 1_000_000,
                        "raw": "one million",
                        "context": "children",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    score = editorial_score(event, NOW)

    assert score >= 55.0


def test_environmental_scale_does_not_get_direct_harm_bonus():
    event = {
        "articles": [
            {
                "title": "Billions of livelihoods threatened by degradation",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["environmental"],
                "scale_numbers": [
                    {
                        "value": 3,
                        "multiplier": 1_000_000_000,
                        "raw": "3 billion",
                        "context": "livelihoods",
                    }
                ],
            }
        ],
        "intelligence": {"score": 60.0},
        "verification": {"verification_score": 42.0},
    }

    score = editorial_score(event, NOW)

    assert score < 55.0


def test_mass_displacement_gets_direct_humanitarian_priority():
    event = {
        "articles": [
            {
                "title": "More than 500,000 people displaced by floods",
                "published_at": "2026-01-01T11:30:00+00:00",
                "event_types": ["flood", "humanitarian"],
                "scale_numbers": [
                    {
                        "value": 500,
                        "multiplier": 1_000,
                        "raw": "500,000",
                        "context": "people",
                    }
                ],
            }
        ],
        "intelligence": {"score": 55.0},
        "verification": {"verification_score": 42.0},
    }

    score = editorial_score(event, NOW)

    assert score >= 50.0
