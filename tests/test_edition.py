from pipeline.edition import (
    build_edition,
    build_editions,
)


def event(
    score=50,
    decision="STANDARD",
    role="BRIEF",
    category="world",
):
    return {
        "title": "Test event",
        "category": category,
        "ranking_score": score,
        "editorial": {
            "decision": decision,
            "role": role,
            "ranking_score": score,
        },
    }


def test_empty_edition():
    result = build_edition([])

    assert result["edition_type"] == "WORLD_PULSE"
    assert result["event_count"] == 0
    assert result["top_story"] is None
    assert result["main_stories"] == []
    assert result["briefs"] == []


def test_top_story_is_selected():
    top = event(
        score=95,
        role="TOP_STORY",
    )

    result = build_edition([top])

    assert result["top_story"] == top
    assert result["event_count"] == 1


def test_main_stories_are_separated():
    events = [
        event(score=80, role="MAIN_STORY"),
        event(score=70, role="MAIN_STORY"),
        event(score=40, role="BRIEF"),
    ]

    result = build_edition(events)

    assert len(result["main_stories"]) == 2
    assert len(result["briefs"]) == 1


def test_top_story_has_priority():
    events = [
        event(score=60, role="BRIEF"),
        event(score=90, role="TOP_STORY"),
        event(score=80, role="MAIN_STORY"),
    ]

    result = build_edition(events)

    assert result["top_story"]["ranking_score"] == 90


def test_main_stories_are_sorted_by_score():
    events = [
        event(score=60, role="MAIN_STORY"),
        event(score=90, role="MAIN_STORY"),
        event(score=75, role="MAIN_STORY"),
    ]

    result = build_edition(events)

    assert [
        item["ranking_score"]
        for item in result["main_stories"]
    ] == [90, 75, 60]


def test_briefs_are_sorted_by_score():
    events = [
        event(score=20, role="BRIEF"),
        event(score=50, role="BRIEF"),
        event(score=35, role="BRIEF"),
    ]

    result = build_edition(events)

    assert [
        item["ranking_score"]
        for item in result["briefs"]
    ] == [50, 35, 20]


def test_rejected_events_are_not_published():
    events = [
        event(score=90, role="TOP_STORY"),
        event(
            score=95,
            role="TOP_STORY",
            decision="REJECT",
        ),
    ]

    result = build_edition(events)

    assert result["event_count"] == 1
    assert result["top_story"]["ranking_score"] == 90


def test_sections_are_created():
    result = build_edition([
        event(
            score=80,
            role="MAIN_STORY",
            category="business",
        ),
        event(
            score=70,
            role="BRIEF",
            category="technology",
        ),
    ])

    assert "business" in result["sections"]
    assert "technology" in result["sections"]

    assert len(result["sections"]["business"]) == 1
    assert len(result["sections"]["technology"]) == 1


def test_category_aliases_are_normalized():
    result = build_edition([
        event(
            score=80,
            category="politics",
        ),
        event(
            score=70,
            category="finance",
        ),
        event(
            score=60,
            category="tech",
        ),
    ])

    assert len(result["sections"]["geopolitics"]) == 1
    assert len(result["sections"]["business"]) == 1
    assert len(result["sections"]["technology"]) == 1


def test_unknown_category_falls_back_to_world():
    result = build_edition([
        event(
            score=50,
            category="something_unknown",
        ),
    ])

    assert len(result["sections"]["world"]) == 1


def test_invalid_input_is_safe():
    assert build_edition(None)["event_count"] == 0
    assert build_edition("invalid")["event_count"] == 0


def test_build_editions_returns_one_edition():
    events = [
        event(score=80, role="MAIN_STORY"),
    ]

    results = build_editions(events)

    assert len(results) == 1
    assert results[0]["event_count"] == 1
