from pipeline.feed_config import (
    FEED_REGISTRY,
    configured_sources,
    get_feeds,
)


def test_feed_registry_contains_core_sources():
    assert "reuters" in FEED_REGISTRY
    assert "associated_press" in FEED_REGISTRY
    assert "bbc" in FEED_REGISTRY
    assert "afp" in FEED_REGISTRY
    assert "un" in FEED_REGISTRY


def test_get_feeds_returns_list():
    feeds = get_feeds()

    assert isinstance(feeds, list)


def test_get_feeds_for_unknown_source_is_empty():
    assert get_feeds(
        "unknown-source"
    ) == []


def test_configured_sources_returns_only_sources_with_feeds():
    sources = configured_sources()

    assert isinstance(sources, list)

    for source in sources:
        assert source in FEED_REGISTRY
        assert FEED_REGISTRY[source]


def test_get_feeds_returns_defensive_copy():
    first = get_feeds()

    first.append(
        {
            "url": "https://example.com/test.xml",
            "source": "Test",
        }
    )

    second = get_feeds()

    assert len(second) < len(first)
