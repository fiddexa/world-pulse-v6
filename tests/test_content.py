from pipeline.content import build_content, build_contents


def _event():
    return {
        "articles": [
            {
                "title": "Major earthquake strikes Nepal",
                "summary": "A powerful earthquake hits Nepal.",
                "published_at": "2026-08-29T10:00:00Z",
                "source": "Reuters",
                "category": "world",
                "locations": ["nepal"],
            },
            {
                "title": "Strong earthquake hits Nepal",
                "summary": "The earthquake causes widespread damage.",
                "published_at": "2026-08-29T10:20:00Z",
                "source": "BBC",
                "category": "world",
                "locations": ["nepal"],
            },
        ],
        "verification": {
            "verification_level": "MULTI_SOURCE",
            "sources": ["reuters", "bbc"],
        },
        "intelligence": {
            "locations": ["nepal"],
        },
        "editorial": {
            "decision": "STANDARD",
        },
    }


def test_build_content_returns_content():
    result = build_content(_event())

    assert "content" in result


def test_content_contains_headline():
    result = build_content(_event())

    assert result["content"]["headline"] == (
        "Major earthquake strikes Nepal"
    )


def test_content_contains_summary():
    result = build_content(_event())

    assert result["content"]["summary"] == (
        "A powerful earthquake hits Nepal."
    )


def test_content_contains_why_it_matters():
    event = _event()
    event["why_it_matters"] = (
        "The earthquake affects communities in Nepal."
    )

    result = build_content(event)

    assert result["content"]["why_it_matters"] == (
        "The earthquake affects communities in Nepal."
    )


def test_why_it_matters_can_come_from_article():
    event = _event()
    event["articles"][0]["why_it_matters"] = (
        "The event affects communities in Nepal."
    )

    result = build_content(event)

    assert result["content"]["why_it_matters"] == (
        "The event affects communities in Nepal."
    )


def test_why_it_matters_is_empty_when_not_supplied():
    result = build_content(_event())

    assert result["content"]["why_it_matters"] == ""


def test_content_contains_section():
    result = build_content(_event())

    assert result["content"]["section"] == "world"


def test_content_contains_verification():
    result = build_content(_event())

    assert result["content"]["verification"] == "MULTI_SOURCE"


def test_content_contains_sources():
    result = build_content(_event())

    assert result["content"]["sources"] == [
        "reuters",
        "bbc",
    ]


def test_content_contains_published_at():
    result = build_content(_event())

    assert result["content"]["published_at"] == (
        "2026-08-29T10:00:00Z"
    )


def test_content_contains_affected_areas():
    result = build_content(_event())

    assert result["content"]["affected_areas"] == ["nepal"]


def test_build_content_preserves_event_data():
    event = _event()

    result = build_content(event)

    assert result["articles"] == event["articles"]
    assert result["verification"] == event["verification"]
    assert result["intelligence"] == event["intelligence"]


def test_build_content_does_not_modify_original():
    event = _event()

    original = dict(event)

    build_content(event)

    assert event == original
    assert "content" not in event


def test_build_contents_handles_multiple_events():
    events = [_event(), _event()]

    result = build_contents(events)

    assert len(result) == 2
    assert all("content" in event for event in result)


def test_invalid_input_is_safe():
    assert build_content(None) == {}
    assert build_contents(None) == []
