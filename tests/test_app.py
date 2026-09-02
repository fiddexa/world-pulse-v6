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


def test_build_edition_from_articles_records_events_in_memory(tmp_path):
    from pipeline.app import build_edition_from_articles
    from pipeline.event_memory import EventMemory

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

    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    edition = build_edition_from_articles(
        articles,
        publication_date="2026-08-30",
        edition_time="07:00",
        event_memory=memory,
    )

    assert edition["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-0700"
    )

    assert edition["event_count"] == 1

    event = edition["top_story"]

    if event is None:
        event = (
            edition["main_stories"]
            + edition["briefs"]
        )[0]

    assert memory.has_seen(event) is True

    assert memory.edition_history(event) == [
        "AROUND-THE-MAIN-EN-2026-08-30-0700"
    ]

    memory.close()


def test_build_edition_from_articles_does_not_require_event_memory():
    from pipeline.app import build_edition_from_articles

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
    ]

    edition = build_edition_from_articles(
        articles,
        publication_date="2026-08-30",
        edition_time="13:00",
    )

    assert edition["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )


def test_process_articles_excludes_information_after_snapshot():
    articles = [
        {
            "title": "Known before seven",
            "published_at": "2026-08-30T06:50:00Z",
            "first_seen_at": "2026-08-30T06:55:00Z",
            "source": "Reuters",
        },
        {
            "title": "Discovered at seven twenty",
            "published_at": "2026-08-30T07:20:00Z",
            "first_seen_at": "2026-08-30T07:20:00Z",
            "source": "BBC",
        },
    ]

    events = process_articles(
        articles,
        editorial_time="2026-08-30T07:00:00Z",
    )

    titles = [
        article.get("original_title", article.get("title"))
        for event in events
        for article in event.get("articles", [])
    ]

    assert "Known before seven" in titles
    assert "Discovered at seven twenty" not in titles


def test_build_edition_uses_publication_slot_as_snapshot_boundary():
    from pipeline.app import build_edition_from_articles

    articles = [
        {
            "title": "Known before seven",
            "published_at": "2026-08-30T06:50:00Z",
            "first_seen_at": "2026-08-30T06:55:00Z",
            "source": "Reuters",
        },
        {
            "title": "Known after seven",
            "published_at": "2026-08-30T11:20:00Z",
            "first_seen_at": "2026-08-30T11:20:00Z",
            "source": "BBC",
        },
    ]

    edition = build_edition_from_articles(
        articles,
        publication_date="2026-08-30",
        edition_time="07:00",
    )

    titles = [
        article.get("original_title", article.get("title"))
        for event in (
            [edition["top_story"]]
            + edition["main_stories"]
            + edition["briefs"]
        )
        if event is not None
        for article in event.get("articles", [])
    ]

    assert "Known before seven" in titles
    assert "Known after seven" not in titles
