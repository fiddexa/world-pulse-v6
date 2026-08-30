from pipeline.feed_config import (
    FEED_REGISTRY,
    all_sources,
    configured_sources,
    get_feeds,
    source_requires_auth,
)


def test_feed_registry_contains_core_sources():
    assert "reuters" in FEED_REGISTRY
    assert "associated_press" in FEED_REGISTRY
    assert "bbc" in FEED_REGISTRY
    assert "afp" in FEED_REGISTRY
    assert "un" in FEED_REGISTRY


def test_get_feeds_returns_list():
    feeds = get_feeds()

    assert isinstance(
        feeds,
        list,
    )


def test_get_feeds_for_unknown_source_is_empty():
    assert get_feeds(
        "unknown-source"
    ) == []


def test_configured_sources_returns_only_sources_with_feeds():
    sources = configured_sources()

    assert isinstance(
        sources,
        list,
    )

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


def test_all_sources_contains_registry_sources():
    sources = all_sources()

    assert isinstance(
        sources,
        list,
    )

    assert set(sources) == set(
        FEED_REGISTRY.keys()
    )


def test_un_feed_is_public_rss():
    feeds = get_feeds("un")

    assert feeds

    for feed in feeds:
        assert feed["type"] == "rss"
        assert feed["requires_auth"] is False
        assert feed["url"].startswith(
            "https://"
        )


def test_sources_without_verified_public_feeds_are_empty():
    assert get_feeds("reuters") == []
    assert get_feeds("associated_press") == []
    assert get_feeds("bbc") == []
    assert get_feeds("afp") == []


def test_source_requires_auth_for_empty_source():
    assert source_requires_auth(
        "bbc"
    ) is False


def test_source_requires_auth_for_unknown_source():
    assert source_requires_auth(
        "unknown-source"
    ) is False


def test_feed_records_have_required_fields():
    for feed in get_feeds():
        assert isinstance(
            feed,
            dict,
        )

        assert feed.get("url")
        assert feed.get("source")
        assert feed.get("type") in {
            "rss",
            "atom",
        }

        assert isinstance(
            feed.get(
                "requires_auth"
            ),
            bool,
        )
