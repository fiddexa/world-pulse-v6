from pipeline.editorial import (
    BRIEF,
    FRONT_PAGE,
    IGNORE,
    IMPORTANT,
    LEAD_STORY,
    SECTION_STORY,
    STANDARD,
    TOP_STORY,
    decide_event,
    decide_events,
    editorial_decision,
    editorial_role,
)


def event(
    ranking_score=50,
    intelligence_score=50,
    verification_score=50,
    verification_level="MULTI_SOURCE",
    breaking=False,
    articles=2,
):
    return {
        "articles": [
            {"title": "Test event"}
            for _ in range(articles)
        ],
        "ranking_score": ranking_score,
        "ranking": {
            "editorial_score": ranking_score,
            "breaking": breaking,
        },
        "intelligence": {
            "score": intelligence_score,
        },
        "verification": {
            "verification_score": verification_score,
            "verification_level": verification_level,
        },
    }


def test_low_score_is_ignored():
    assert editorial_decision(
        event(ranking_score=20)
    ) == IGNORE


def test_standard_story():
    assert editorial_decision(
        event(ranking_score=45)
    ) == STANDARD


def test_important_story():
    assert editorial_decision(
        event(ranking_score=60)
    ) == IMPORTANT


def test_top_story_requires_verification():
    assert editorial_decision(
        event(
            ranking_score=75,
            verification_level="MULTI_SOURCE",
        )
    ) == TOP_STORY


def test_high_score_and_confirmation_can_reach_front_page():
    assert editorial_decision(
        event(
            ranking_score=90,
            verification_level="WIDELY_CONFIRMED",
        )
    ) == FRONT_PAGE


def test_breaking_major_event_reaches_front_page():
    assert editorial_decision(
        event(
            ranking_score=70,
            intelligence_score=80,
            verification_level="MULTI_SOURCE",
            breaking=True,
        )
    ) == FRONT_PAGE


def test_unconfirmed_breaking_event_is_not_front_page():
    assert editorial_decision(
        event(
            ranking_score=90,
            intelligence_score=90,
            verification_level="UNCONFIRMED",
            breaking=True,
        )
    ) != FRONT_PAGE


def test_roles():
    assert editorial_role(event(ranking_score=90),
                          FRONT_PAGE) == LEAD_STORY

    assert editorial_role(event(ranking_score=75),
                          TOP_STORY) == SECTION_STORY

    assert editorial_role(event(ranking_score=45),
                          STANDARD) == BRIEF


def test_decide_event_returns_structured_metadata():
    result = decide_event(
        event(
            ranking_score=75,
            intelligence_score=70,
            verification_score=80,
        )
    )

    assert "decision" in result
    assert "role" in result
    assert result["ranking_score"] == 75.0
    assert result["intelligence_score"] == 70.0
    assert result["verification_score"] == 80.0


def test_decide_event_does_not_modify_original():
    original = event(ranking_score=60)
    before = dict(original)

    decide_event(original)

    assert original == before


def test_decide_events_preserves_events():
    events = [
        event(ranking_score=80),
        event(ranking_score=40),
    ]

    results = decide_events(events)

    assert len(results) == 2
    assert "articles" in results[0]
    assert "editorial" in results[0]
    assert "editorial" in results[1]


def test_invalid_input_is_safe():
    assert editorial_decision(None) == IGNORE
    assert decide_event(None)["decision"] == IGNORE
    assert decide_events(None) == []
