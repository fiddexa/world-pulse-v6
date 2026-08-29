from pipeline.sources import (
    get_source,
    is_primary_source,
    list_sources,
    normalize_source_name,
    source_categories,
    source_exists,
    source_independence,
    source_profile,
    source_reputation,
    source_supports_category,
    source_tier,
)


def test_normalize_source_name():
    assert normalize_source_name(
        "  Reuters  "
    ) == "reuters"


def test_registered_source_exists():
    assert source_exists("Reuters")
    assert source_exists("reuters.com")


def test_unknown_source_does_not_exist():
    assert not source_exists(
        "Unknown News Network"
    )


def test_reuters_has_major_media_tier():
    assert source_tier("Reuters") == 2


def test_un_is_primary_source():
    assert is_primary_source(
        "United Nations"
    )


def test_reuters_is_not_primary_source():
    assert not is_primary_source(
        "Reuters"
    )


def test_reputation_is_bounded():
    for source in (
        "Reuters",
        "BBC",
        "United Nations",
        "Unknown News Network",
    ):
        score = source_reputation(source)

        assert 0 <= score <= 10


def test_independence_is_bounded():
    for source in (
        "Reuters",
        "BBC",
        "United Nations",
        "Unknown News Network",
    ):
        score = source_independence(source)

        assert 0 <= score <= 10


def test_unknown_source_is_conservative():
    assert source_tier(
        "Unknown News Network"
    ) == 4

    assert source_reputation(
        "Unknown News Network"
    ) == 0

    assert source_independence(
        "Unknown News Network"
    ) == 0

    assert not is_primary_source(
        "Unknown News Network"
    )


def test_source_categories():
    categories = source_categories(
        "Reuters"
    )

    assert "world" in categories
    assert "economy" in categories


def test_source_supports_category():
    assert source_supports_category(
        "Reuters",
        "economy",
    )

    assert not source_supports_category(
        "Reuters",
        "unknown_category",
    )


def test_source_profile_is_complete():
    profile = source_profile("Reuters")

    assert profile["name"] == "Reuters"
    assert profile["domain"] == "reuters.com"
    assert profile["tier"] == 2
    assert profile["reputation_score"] > 0
    assert profile["independence_score"] > 0
    assert profile["primary_source"] is False


def test_get_source_returns_copy():
    first = get_source("Reuters")
    first["name"] = "Changed"

    second = get_source("Reuters")

    assert second["name"] == "Reuters"


def test_list_sources_returns_registered_sources():
    sources = list_sources()

    assert isinstance(sources, list)
    assert len(sources) >= 10


def test_source_categories_are_defensive_copy():
    categories = source_categories(
        "Reuters"
    )

    categories.append("fake")

    assert "fake" not in source_categories(
        "Reuters"
    )
