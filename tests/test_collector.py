from pipeline.collector import (
    _parse_date,
    collect_feeds,
    deduplicate_articles,
    fetch_feed,
)


def test_parse_rss_date():
    result = _parse_date(
        "Tue, 25 Aug 2026 10:00:00 GMT"
    )

    assert result is not None
    assert result.startswith(
        "2026-08-25T10:00:00"
    )


def test_parse_iso_date():
    result = _parse_date(
        "2026-08-25T10:00:00Z"
    )

    assert result is not None
    assert result.startswith(
        "2026-08-25T10:00:00"
    )


def test_parse_invalid_date():
    assert _parse_date(
        "not-a-date"
    ) is None


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

    result = deduplicate_articles(
        articles
    )

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

    result = deduplicate_articles(
        articles
    )

    assert len(result) == 2


def test_invalid_feed_returns_empty():
    result = fetch_feed(
        "not-a-valid-url"
    )

    assert result == []


def test_collect_feeds_processes_all_feeds(
    monkeypatch,
):
    calls = []

    def fake_fetch_feed(
        feed_url,
        source=None,
        timeout=15,
    ):
        calls.append(
            (
                feed_url,
                source,
                timeout,
            )
        )

        return [
            {
                "title": f"Article from {source}",
                "source": source,
                "url": feed_url,
            }
        ]

    monkeypatch.setattr(
        "pipeline.collector.fetch_feed",
        fake_fetch_feed,
    )

    feeds = [
        {
            "url": "https://example.com/a.xml",
            "source": "Source A",
        },
        {
            "url": "https://example.com/b.xml",
            "source": "Source B",
        },
        {
            "url": "https://example.com/c.xml",
            "source": "Source C",
        },
    ]

    result = collect_feeds(
        feeds,
        timeout=7,
    )

    assert len(calls) == 3

    assert calls == [
        (
            "https://example.com/a.xml",
            "Source A",
            7,
        ),
        (
            "https://example.com/b.xml",
            "Source B",
            7,
        ),
        (
            "https://example.com/c.xml",
            "Source C",
            7,
        ),
    ]

    assert len(result) == 3

    assert result[0]["source"] == "Source A"
    assert result[1]["source"] == "Source B"
    assert result[2]["source"] == "Source C"


def test_collect_feeds_supports_string_urls(
    monkeypatch,
):
    calls = []

    def fake_fetch_feed(
        feed_url,
        source=None,
        timeout=15,
    ):
        calls.append(
            (
                feed_url,
                source,
                timeout,
            )
        )

        return [
            {
                "title": "Test article",
                "source": source,
                "url": feed_url,
            }
        ]

    monkeypatch.setattr(
        "pipeline.collector.fetch_feed",
        fake_fetch_feed,
    )

    result = collect_feeds(
        [
            "https://example.com/a.xml",
            "https://example.com/b.xml",
        ]
    )

    assert len(calls) == 2

    assert calls[0] == (
        "https://example.com/a.xml",
        None,
        15,
    )

    assert calls[1] == (
        "https://example.com/b.xml",
        None,
        15,
    )

    assert len(result) == 2


def test_collect_feeds_invalid_input_returns_empty():
    assert collect_feeds(
        None
    ) == []

    assert collect_feeds(
        "https://example.com/feed.xml"
    ) == []

def test_fetch_feed_supports_gzip_response(
    monkeypatch,
):
    import gzip

    from io import BytesIO

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

        def read(self):
            xml = b"""
            <rss version="2.0">
                <channel>
                    <item>
                        <title>GZIP Test Article</title>
                        <description>Test summary</description>
                        <pubDate>Tue, 25 Aug 2026 10:00:00 GMT</pubDate>
                        <link>https://example.com/gzip</link>
                    </item>
                </channel>
            </rss>
            """

            return gzip.compress(xml)

    def fake_urlopen(
        request,
        timeout=15,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        "pipeline.collector.urlopen",
        fake_urlopen,
    )

    result = fetch_feed(
        "https://example.com/feed.xml",
        source="Test",
    )

    assert len(result) == 1
    assert result[0]["title"] == (
        "GZIP Test Article"
    )
    assert result[0]["source"] == "Test"
