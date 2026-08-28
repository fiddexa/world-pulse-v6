from pipeline.ranking import (
    calculate_ranking_score,
    ranking_significance,
    rank_events,
)


def make_event(
    intelligence_score,
    verification_level="MULTI_SOURCE",
    independent_sources=2,
    event_type="DIRECT_EVENT",
):
    return {
        "title": "Test event",
        "articles": [
            {
                "title": "Test event",
                "source": "Reuters",
            }
        ],
        "event_type": event_type,
        "intelligence": {
            "score": intelligence_score,
        },
        "verification": {
            "verification_level": verification_level,
            "independent_sources": independent_sources,
            "agreement": 0.8,
            "source_diversity_score": 8.0,
            "perspective_diversity": 7.0,
        },
    }


def test_ranking_uses_intelligence():
    low = make_event(30)
    high = make_event(80)

    assert calculate_ranking_score(high) > calculate_ranking_score(low)


def test_verification_has_moderate_effect():
    weak = make_event(
        70,
        verification_level="SINGLE_SOURCE",
        independent_sources=1,
    )

    strong = make_event(
        70,
        verification_level="WIDELY_CONFIRMED",
        independent_sources=4,
    )

    difference = (
        calculate_ranking_score(strong)
        - calculate_ranking_score(weak)
    )

    assert difference > 0
    assert difference < 15


def test_single_source_cannot_be_critical():
    event = make_event(
        100,
        verification_level="SINGLE_SOURCE",
        independent_sources=1,
    )

    score = calculate_ranking_score(event)

    assert score < 90


def test_two_sources_cannot_be_critical():
    event = make_event(
        100,
        verification_level="MULTI_SOURCE",
        independent_sources=2,
    )

    score = calculate_ranking_score(event)

    assert score < 90


def test_three_sources_cannot_be_critical():
    event = make_event(
        100,
        verification_level="MULTI_SOURCE",
        independent_sources=3,
    )

    score = calculate_ranking_score(event)

    assert score < 90


def test_real_event_can_reach_critical():
    event = make_event(
        100,
        verification_level="WIDELY_CONFIRMED",
        independent_sources=5,
    )

    score = calculate_ranking_score(event)

    assert score >= 90


def test_analysis_is_penalized():
    direct = make_event(
        80,
        event_type="DIRECT_EVENT",
    )

    analysis = make_event(
        80,
        event_type="ANALYSIS",
    )

    assert calculate_ranking_score(direct) > calculate_ranking_score(
        analysis
    )


def test_forecast_is_penalized():
    direct = make_event(
        80,
        event_type="DIRECT_EVENT",
    )

    forecast = make_event(
        80,
        event_type="FORECAST",
    )

    assert calculate_ranking_score(direct) > calculate_ranking_score(
        forecast
    )


def test_opinion_is_strongly_penalized():
    direct = make_event(
        80,
        event_type="DIRECT_EVENT",
    )

    opinion = make_event(
        80,
        event_type="OPINION",
    )

    assert calculate_ranking_score(direct) > calculate_ranking_score(
        opinion
    )


def test_ranking_score_is_bounded():
    event = make_event(100)

    score = calculate_ranking_score(event)

    assert 0 <= score <= 100


def test_significance_comes_only_from_ranking_score():
    assert ranking_significance(95) == "CRITICAL"
    assert ranking_significance(80) == "VERY HIGH"
    assert ranking_significance(65) == "HIGH"
    assert ranking_significance(50) == "MEDIUM"
    assert ranking_significance(49.99) == "LOW"


def test_rank_events_orders_by_ranking_score():
    events = [
        make_event(40),
        make_event(90),
        make_event(60),
    ]

    ranked = rank_events(events)

    scores = [
        event["ranking_score"]
        for event in ranked
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_ranking_does_not_modify_intelligence_score():
    event = make_event(75)
    original = event["intelligence"]["score"]

    calculate_ranking_score(event)

    assert event["intelligence"]["score"] == original
