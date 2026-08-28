from pipeline.app import process_articles


def test_full_pipeline_produces_ranked_events():
    articles = [
        {
            "title": "Major earthquake strikes Nepal",
            "summary": "A powerful earthquake hits Nepal.",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
        {
            "title": "Strong earthquake hits Nepal",
            "summary": "The earthquake causes widespread damage.",
            "published_at": "2026-08-28T10:20:00Z",
            "source": "BBC",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
    ]

    events = process_articles(articles)

    assert len(events) == 1

    event = events[0]

    assert len(event["articles"]) == 2
    assert "verification" in event
    assert "intelligence" in event
    assert "ranking_score" in event
    assert "ranking_significance" in event


def test_pipeline_keeps_different_events_separate():
    articles = [
        {
            "title": "Earthquake strikes Nepal",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
        },
        {
            "title": "Earthquake strikes Japan",
            "published_at": "2026-08-28T10:10:00Z",
            "source": "BBC",
        },
    ]

    events = process_articles(articles)

    assert len(events) == 2


def test_pipeline_returns_empty_for_empty_input():
    assert process_articles([]) == []


def test_pipeline_does_not_crash_on_invalid_items():
    articles = [
        None,
        {},
        "invalid",
        {
            "title": "Earthquake strikes Nepal",
            "source": "Reuters",
        },
    ]

    events = process_articles(articles)

    assert isinstance(events, list)
