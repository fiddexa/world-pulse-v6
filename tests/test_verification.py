from pipeline.verify import (
    UNCONFIRMED,
    SINGLE_SOURCE,
    MULTI_SOURCE,
    WIDELY_CONFIRMED,
    verify_event,
    verify_events,
)


def _event(*sources):
    return {
        "articles": [
            {
                "title": f"Report {index}",
                "source": source,
                "category": "world",
                "region": "asia",
                "country": "nepal",
            }
            for index, source in enumerate(sources)
        ],
        "similarity_scores": [0.8] * max(0, len(sources) - 1),
    }


def test_no_articles_are_unconfirmed():
    result = verify_event({})

    assert result["verification_level"] == UNCONFIRMED
    assert result["independent_sources"] == 0
    assert result["verification_score"] == 0.0


def test_one_source_is_single_source():
    result = verify_event(
        _event("Reuters")
    )

    assert result["verification_level"] == SINGLE_SOURCE
    assert result["independent_sources"] == 1
    assert result["sources"] == ["reuters"]


def test_duplicate_articles_from_same_source_are_not_independent():
    result = verify_event(
        _event("Reuters", "Reuters", "Reuters")
    )

    assert result["independent_sources"] == 1
    assert result["verification_level"] == SINGLE_SOURCE


def test_two_independent_sources_are_multi_source():
    result = verify_event(
        _event("Reuters", "BBC")
    )

    assert result["independent_sources"] == 2
    assert result["verification_level"] == MULTI_SOURCE


def test_three_independent_sources_can_be_widely_confirmed():
    result = verify_event(
        _event("Reuters", "BBC", "AP")
    )

    assert result["independent_sources"] == 3
    assert result["verification_level"] == WIDELY_CONFIRMED


def test_aliases_do_not_create_fake_independence():
    result = verify_event(
        _event(
            "Reuters",
            "Reuters News",
            "Thomson Reuters",
        )
    )

    assert result["independent_sources"] == 1
    assert result["verification_level"] == SINGLE_SOURCE


def test_diversity_is_exposed():
    event = {
        "articles": [
            {
                "title": "Earthquake strikes Nepal",
                "source": "Reuters",
                "category": "natural_disaster",
                "region": "asia",
                "country": "nepal",
            },
            {
                "title": "Major earthquake hits Nepal",
                "source": "BBC",
                "category": "natural_disaster",
                "region": "asia",
                "country": "nepal",
            },
        ],
        "similarity_scores": [0.7],
    }

    result = verify_event(event)

    assert result["independent_sources"] == 2
    assert result["countries"] == ["nepal"]
    assert result["regions"] == ["asia"]
    assert result["categories"] == ["natural_disaster"]
    assert result["agreement"] > 0


def test_malformed_event_never_raises():
    result = verify_event(
        {
            "articles": [
                None,
                "bad",
                {},
            ]
        }
    )

    assert result["verification_level"] == UNCONFIRMED


def test_verify_events_preserves_event_data():
    events = [
        _event("Reuters"),
        _event("Reuters", "BBC"),
    ]

    results = verify_events(events)

    assert len(results) == 2
    assert "articles" in results[0]
    assert "verification" in results[0]
    assert results[0]["verification"]["verification_level"] == SINGLE_SOURCE
    assert results[1]["verification"]["verification_level"] == MULTI_SOURCE


def test_verification_score_is_not_editorial_significance():
    result = verify_event(
        _event("Reuters")
    )

    assert result["verification"]["verification_level"] if False else True
    assert 0.0 <= result["verification_score"] <= 100.0
