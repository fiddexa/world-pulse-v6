from pipeline.publication import (
    build_publication,
    build_publications,
)


def event():
    return {
        "content": {
            "headline": "Major earthquake strikes Nepal",
            "summary": "A powerful earthquake hits Nepal.",
            "section": "world",
            "verification": "MULTI_SOURCE",
            "sources": ["bbc", "reuters"],
            "published_at": "2026-08-29T10:00:00Z",
            "affected_areas": ["nepal"],
        }
    }


def test_build_publication_adds_publication():
    result = build_publication(event())

    assert "publication" in result


def test_telegram_contains_headline():
    result = build_publication(event())

    assert "Major earthquake strikes Nepal" in (
        result["publication"]["telegram"]
    )


def test_telegram_contains_summary():
    result = build_publication(event())

    assert "A powerful earthquake hits Nepal." in (
        result["publication"]["telegram"]
    )


def test_telegram_contains_verification():
    result = build_publication(event())

    assert "MULTI_SOURCE" in (
        result["publication"]["telegram"]
    )


def test_telegram_contains_sources():
    result = build_publication(event())

    telegram = result["publication"]["telegram"]

    assert "bbc" in telegram
    assert "reuters" in telegram


def test_website_contains_structured_fields():
    result = build_publication(event())

    website = result["publication"]["website"]

    assert website["headline"] == (
        "Major earthquake strikes Nepal"
    )
    assert website["summary"] == (
        "A powerful earthquake hits Nepal."
    )
    assert website["section"] == "world"


def test_website_contains_sources():
    result = build_publication(event())

    assert result["publication"]["website"]["sources"] == [
        "bbc",
        "reuters",
    ]


def test_website_contains_affected_areas():
    result = build_publication(event())

    assert result["publication"]["website"]["affected_areas"] == [
        "nepal",
    ]


def test_publication_preserves_original_event():
    original = event()

    result = build_publication(original)

    assert result["content"] == original["content"]


def test_build_publication_does_not_modify_original():
    original = event()
    before = dict(original)

    build_publication(original)

    assert original == before
    assert "publication" not in original


def test_build_publications_handles_multiple_events():
    result = build_publications([
        event(),
        event(),
    ])

    assert len(result) == 2
    assert all(
        "publication" in item
        for item in result
    )


def test_invalid_input_is_safe():
    assert build_publication(None) == {}
    assert build_publications(None) == []
