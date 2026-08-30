from pipeline.edition_publication import (
    build_edition_publication,
    build_edition_publications,
)


def event(
    headline,
    telegram,
    section="world",
    role="BRIEF",
):
    return {
        "editorial": {
            "role": role,
        },
        "content": {
            "headline": headline,
            "section": section,
        },
        "publication": {
            "telegram": telegram,
        },
    }


def edition():
    top = event(
        "Top story",
        "TOP STORY TEXT",
        section="geopolitics",
        role="TOP_STORY",
    )

    main = event(
        "Main story",
        "MAIN STORY TEXT",
        section="business",
        role="MAIN_STORY",
    )

    brief = event(
        "Brief story",
        "BRIEF STORY TEXT",
        section="business",
        role="BRIEF",
    )

    return {
        "edition_id": "20260829-2300-en",
        "edition_type": "WORLD_PULSE",
        "event_count": 3,
        "top_story": top,
        "main_stories": [main],
        "briefs": [brief],
        "sections": {
            "geopolitics": [top],
            "business": [main, brief],
        },
    }


def test_build_edition_publication_returns_package():
    result = build_edition_publication(edition())

    assert result["edition_id"] == "20260829-2300-en"
    assert result["edition_type"] == "WORLD_PULSE"
    assert result["event_count"] == 3


def test_telegram_package_exists():
    result = build_edition_publication(edition())

    assert result["telegram"]["channel"] == "telegram"


def test_telegram_contains_all_event_publications():
    result = build_edition_publication(edition())

    text = result["telegram"]["text"]

    assert "TOP STORY TEXT" in text
    assert "MAIN STORY TEXT" in text
    assert "BRIEF STORY TEXT" in text


def test_telegram_contains_edition_header():
    result = build_edition_publication(edition())

    text = result["telegram"]["text"]

    assert "WORLD PULSE" in text
    assert "Edition 20260829-2300-en" in text


def test_sections_are_grouped():
    result = build_edition_publication(edition())

    text = result["telegram"]["text"]

    assert "GEOPOLITICS" in text
    assert "BUSINESS" in text


def test_event_metadata_is_preserved_in_package():
    result = build_edition_publication(edition())

    events = result["telegram"]["events"]

    assert events[0]["role"] == "TOP_STORY"
    assert events[0]["section"] == "geopolitics"
    assert events[0]["headline"] == "Top story"


def test_only_events_with_telegram_content_are_published():
    item = edition()

    item["briefs"].append(
        event(
            "No telegram",
            "",
            section="culture",
        )
    )

    result = build_edition_publication(item)

    assert result["telegram"]["event_count"] == 3
    assert "No telegram" not in result["telegram"]["text"]


def test_original_edition_is_not_modified():
    item = edition()

    before = {
        "edition_id": item["edition_id"],
        "event_count": item["event_count"],
        "top_story": item["top_story"],
        "main_stories": item["main_stories"],
        "briefs": item["briefs"],
    }

    build_edition_publication(item)

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]
    assert item["main_stories"] == before["main_stories"]
    assert item["briefs"] == before["briefs"]


def test_invalid_input_is_safe():
    assert build_edition_publication(None) == {}
    assert build_edition_publication("invalid") == {}


def test_multiple_editions():
    result = build_edition_publications(
        [edition(), edition()]
    )

    assert len(result) == 2
    assert all(
        item["edition_type"] == "WORLD_PULSE"
        for item in result
    )


def test_invalid_multiple_editions_input_is_safe():
    assert build_edition_publications(None) == []
    assert build_edition_publications("invalid") == []
