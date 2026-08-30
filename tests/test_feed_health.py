from pipeline.feed_health import (
    EMPTY,
    FAILED,
    OK,
    check_feed,
    check_feeds,
    summarize_health,
)


def feed():
    return {
        "url": "https://example.com/feed.xml",
        "source": "Example",
        "type": "rss",
        "requires_auth": False,
    }


def test_check_feed_ok():
    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        return [
            {"title": "Article 1"},
            {"title": "Article 2"},
        ]

    result = check_feed(
        feed(),
        fetcher=fake_fetcher,
    )

    assert result["status"] == OK
    assert result["article_count"] == 2
    assert result["source"] == "Example"


def test_check_feed_empty():
    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        return []

    result = check_feed(
        feed(),
        fetcher=fake_fetcher,
    )

    assert result["status"] == EMPTY
    assert result["article_count"] == 0


def test_check_feed_fetch_failure():
    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        raise RuntimeError("network failure")

    result = check_feed(
        feed(),
        fetcher=fake_fetcher,
    )

    assert result["status"] == FAILED
    assert result["article_count"] == 0


def test_check_feed_invalid_result():
    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        return None

    result = check_feed(
        feed(),
        fetcher=fake_fetcher,
    )

    assert result["status"] == FAILED


def test_check_feed_invalid_feed():
    result = check_feed(
        {},
        fetcher=lambda *args, **kwargs: [],
    )

    assert result["status"] == FAILED


def test_check_feeds_checks_all_feeds():
    calls = []

    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        calls.append(url)

        return [
            {"title": url}
        ]

    feeds = [
        {
            "url": "https://example.com/a.xml",
            "source": "A",
        },
        {
            "url": "https://example.com/b.xml",
            "source": "B",
        },
        {
            "url": "https://example.com/c.xml",
            "source": "C",
        },
    ]

    results = check_feeds(
        feeds,
        fetcher=fake_fetcher,
    )

    assert len(results) == 3
    assert len(calls) == 3

    assert all(
        result["status"] == OK
        for result in results
    )


def test_check_feeds_isolates_failures():
    def fake_fetcher(
        url,
        source=None,
        timeout=15,
    ):
        if url.endswith("b.xml"):
            raise RuntimeError("failure")

        return [
            {"title": "Article"}
        ]

    feeds = [
        {
            "url": "https://example.com/a.xml",
            "source": "A",
        },
        {
            "url": "https://example.com/b.xml",
            "source": "B",
        },
        {
            "url": "https://example.com/c.xml",
            "source": "C",
        },
    ]

    results = check_feeds(
        feeds,
        fetcher=fake_fetcher,
    )

    assert [
        result["status"]
        for result in results
    ] == [
        OK,
        FAILED,
        OK,
    ]


def test_check_feeds_invalid_input():
    assert check_feeds(
        None,
        fetcher=lambda *args, **kwargs: [],
    ) == []


def test_summarize_health():
    results = [
        {"status": OK},
        {"status": OK},
        {"status": EMPTY},
        {"status": FAILED},
        {"status": FAILED},
    ]

    summary = summarize_health(
        results
    )

    assert summary == {
        "total": 5,
        "ok": 2,
        "empty": 1,
        "failed": 2,
    }


def test_summarize_health_empty():
    assert summarize_health(
        []
    ) == {
        "total": 0,
        "ok": 0,
        "empty": 0,
        "failed": 0,
    }
