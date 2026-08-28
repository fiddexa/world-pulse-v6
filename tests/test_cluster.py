from pipeline.cluster import cluster_articles


def test_same_event_clusters_together():
    articles = [
        {
            "title": "Earthquake strikes Nepal",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
        },
        {
            "title": "Major earthquake hits Nepal",
            "published_at": "2026-08-28T10:20:00Z",
            "source": "BBC",
        },
    ]

    events = cluster_articles(articles)

    assert len(events) == 1
    assert len(events[0]["articles"]) == 2


def test_different_locations_stay_separate():
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

    events = cluster_articles(articles)

    assert len(events) == 2


def test_different_event_types_stay_separate():
    articles = [
        {
            "title": "Earthquake strikes Nepal",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
        },
        {
            "title": "Floods hit Nepal",
            "published_at": "2026-08-28T10:10:00Z",
            "source": "BBC",
        },
    ]

    events = cluster_articles(articles)

    assert len(events) == 2


def test_same_event_different_wording():
    articles = [
        {
            "title": "Two UN peacekeepers killed in South Sudan",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
        },
        {
            "title": "South Sudan ambush kills UN peacekeepers",
            "published_at": "2026-08-28T10:15:00Z",
            "source": "BBC",
        },
    ]

    events = cluster_articles(articles)

    assert len(events) == 1
    assert len(events[0]["articles"]) == 2


def test_empty_input():
    assert cluster_articles([]) == []
