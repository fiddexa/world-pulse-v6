from pipeline.intelligence import (
    analyze_event,
    analyze_events,
    intelligence_level,
    intelligence_score,
)


def _event(
    event_types=None,
    locations=None,
    casualties=None,
    articles=1,
):
    article = {
        "title": "Test event",
        "event_types": event_types or [],
        "locations": locations or [],
        "casualty_numbers": casualties or [],
    }

    return {
        "articles": [article for _ in range(articles)],
    }


def test_empty_event_has_zero_score():
    assert intelligence_score({}) == 0.0


def test_invalid_event_has_zero_score():
    assert intelligence_score(None) == 0.0


def test_high_impact_event_scores_higher_than_minor_event():
    minor = _event(
        event_types=["political"],
        locations=["nepal"],
    )

    major = _event(
        event_types=["earthquake"],
        locations=["nepal"],
        casualties=["100"],
    )

    assert intelligence_score(major) > intelligence_score(minor)


def test_casualties_increase_impact():
    one = _event(
        event_types=["attack"],
        locations=["ukraine"],
        casualties=["1"],
    )

    many = _event(
        event_types=["attack"],
        locations=["ukraine"],
        casualties=["100"],
    )

    assert intelligence_score(many) > intelligence_score(one)


def test_geographic_scope_increases_score():
    local = _event(
        event_types=["flood"],
        locations=["nepal"],
    )

    broad = _event(
        event_types=["flood"],
        locations=["nepal", "india", "china"],
    )

    assert intelligence_score(broad) > intelligence_score(local)


def test_score_is_bounded():
    event = _event(
        event_types=["earthquake"],
        locations=[
            "nepal",
            "india",
            "china",
            "pakistan",
            "bangladesh",
        ],
        casualties=["100000"],
        articles=10,
    )

    score = intelligence_score(event)

    assert 0.0 <= score <= 100.0


def test_level_boundaries():
    assert intelligence_level(0) == "LOW"
    assert intelligence_level(30) == "MEDIUM"
    assert intelligence_level(50) == "HIGH"
    assert intelligence_level(65) == "VERY_HIGH"
    assert intelligence_level(80) == "CRITICAL"


def test_verification_does_not_affect_intelligence():
    event_a = _event(
        event_types=["earthquake"],
        locations=["nepal"],
        casualties=["50"],
    )

    event_b = dict(event_a)
    event_b["verification"] = {
        "verification_score": 100,
        "independent_sources": 10,
        "verification_level": "WIDELY_CONFIRMED",
    }

    assert intelligence_score(event_a) == intelligence_score(event_b)


def test_analyze_event_returns_structured_result():
    event = _event(
        event_types=["earthquake"],
        locations=["nepal"],
        casualties=["10"],
        articles=2,
    )

    result = analyze_event(event)

    assert "score" in result
    assert "level" in result
    assert "event_types" in result
    assert "locations" in result
    assert result["maximum_casualty_number"] == 10.0
    assert result["article_count"] == 2


def test_analyze_events_preserves_events():
    events = [
        _event(
            event_types=["flood"],
            locations=["nepal"],
        ),
        _event(
            event_types=["earthquake"],
            locations=["japan"],
            casualties=["20"],
        ),
    ]

    results = analyze_events(events)

    assert len(results) == 2
    assert "articles" in results[0]
    assert "intelligence" in results[0]
    assert "intelligence" in results[1]


def test_large_population_scale_increases_impact():
    small = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    large = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    large["articles"][0]["scale_numbers"] = [
        {
            "value": 1,
            "multiplier": 1_000_000,
            "raw": "one million",
            "context": "children",
        }
    ]

    assert intelligence_score(large) > intelligence_score(small)


def test_scale_numbers_do_not_count_as_casualties():
    event = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 3.7,
            "multiplier": 1_000_000,
            "raw": "3.7 million",
            "context": "children",
        }
    ]

    result = analyze_event(event)

    assert result["maximum_scale_number"] == 3_700_000.0
    assert result["maximum_casualty_number"] == 0.0


def test_million_scale_gets_strong_scale_score():
    event = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 1,
            "multiplier": 1_000_000,
            "raw": "one million",
            "context": "children",
        }
    ]

    result = analyze_event(event)

    assert result["scale_score"] == 25.0


def test_large_humanitarian_scale_reaches_high_impact():
    event = _event(
        event_types=["health", "humanitarian"],
        locations=["afghanistan"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 3.7,
            "multiplier": 1_000_000,
            "raw": "3.7 million",
            "context": "children",
        }
    ]

    result = analyze_event(event)

    assert result["maximum_scale_number"] == 3_700_000.0
    assert result["scale_score"] >= 25.0
    assert result["score"] >= 50.0


def test_population_scale_is_not_casualty_impact():
    event = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 3.7,
            "multiplier": 1_000_000,
            "raw": "3.7 million",
            "context": "children",
        }
    ]

    result = analyze_event(event)

    assert result["maximum_scale_number"] == 3_700_000.0
    assert result["maximum_casualty_number"] == 0.0


def test_mass_displacement_has_scale_impact():
    event = _event(
        event_types=["humanitarian"],
        locations=["nepal"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 500,
            "multiplier": 1_000,
            "raw": "500,000",
            "context": "people",
        }
    ]

    result = analyze_event(event)

    assert result["maximum_scale_number"] == 500_000.0
    assert result["scale_score"] >= 20.0


def test_malnutrition_scale_gets_humanitarian_bonus():
    event = _event(
        event_types=["health", "humanitarian"],
        locations=["afghanistan"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 3.7,
            "multiplier": 1_000_000,
            "raw": "3.7 million",
            "context": "children",
        }
    ]

    result = analyze_event(event)

    assert result["scale_score"] >= 25.0


def test_displaced_population_is_recognized_as_mass_impact():
    event = _event(
        event_types=["humanitarian"],
        locations=["nepal"],
    )

    event["articles"][0]["scale_numbers"] = [
        {
            "value": 500,
            "multiplier": 1_000,
            "raw": "500,000",
            "context": "people",
        }
    ]

    result = analyze_event(event)

    assert result["scale_score"] >= 20.0


def test_large_livelihood_scale_does_not_equal_direct_humanitarian_harm():
    humanitarian = _event(
        event_types=["health", "humanitarian"],
        locations=["afghanistan"],
    )

    humanitarian["articles"][0]["scale_numbers"] = [
        {
            "value": 3.7,
            "multiplier": 1_000_000,
            "raw": "3.7 million",
            "context": "children",
        }
    ]

    economic = _event(
        event_types=["humanitarian"],
        locations=["afghanistan"],
    )

    economic["articles"][0]["scale_numbers"] = [
        {
            "value": 3,
            "multiplier": 1_000_000_000,
            "raw": "3 billion",
            "context": "livelihoods",
        }
    ]

    humanitarian_result = analyze_event(humanitarian)
    economic_result = analyze_event(economic)

    assert humanitarian_result["scale_score"] >= economic_result["scale_score"]
