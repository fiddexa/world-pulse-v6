from pipeline.collector import (
    _parse_date,
    deduplicate_articles,
    fetch_feed,
)


def test_parse_rss_date():
    result = _parse_date(
        "Tue, 25 Aug 2026 10:00:00 GMT"
    )

    assert result is not None
    assert result.startswith("2026-08-25T10:00:00")


def test_parse_iso_date():
    result = _parse_date(
        "2026-08-25T10:00:00Z"
    )

    assert result is not None
    assert result.startswith("2026-08-25T10:00:00")


def test_parse_invalid_date():
    assert _parse_date("not-a-date") is None


def test_deduplicate_by_url():
    articles = [
        {
            "title": "First",
            "source": "Test",
            "url": "https://example.com/a",
        },
        {
            "title": "Same article",
            "source": "Other",
            "url": "https://example.com/a",
        },
        {
            "title": "Second",
            "source": "Test",
            "url": "https://example.com/b",
        },
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 2
    assert result[0]["title"] == "First"
    assert result[1]["title"] == "Second"


def test_deduplicate_without_url():
    articles = [
        {
            "title": "Same story",
            "source": "Reuters",
            "url": "",
        },
        {
            "title": "Same story",
            "source": "Reuters",
            "url": "",
        },
        {
            "title": "Different story",
            "source": "Reuters",
            "url": "",
        },
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 2


def test_invalid_feed_returns_empty():
    result = fetch_feed(
        "not-a-valid-url"
    )

    assert result == []
