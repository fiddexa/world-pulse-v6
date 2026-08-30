from pipeline.edition_runner import run_edition
from pipeline.event_memory import EventMemory


def articles():
    return [
        {
            "title": "Major earthquake strikes Nepal",
            "summary": "A powerful earthquake hits Nepal.",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
        {
            "title": "Strong earthquake hits Nepal",
            "summary": "The earthquake causes widespread damage.",
            "published_at": "2026-08-28T10:20:00Z",
            "source": "BBC",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
    ]


def test_run_edition_builds_stable_edition():
    memory = EventMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "07:00",
        event_memory=memory,
    )

    assert edition["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-0700"
    )

    assert edition["event_count"] == 1

    memory.close()


def test_run_edition_records_event_in_memory():
    memory = EventMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "13:00",
        event_memory=memory,
    )

    event = edition["top_story"]

    if event is None:
        event = (
            edition["main_stories"]
            + edition["briefs"]
        )[0]

    assert memory.has_seen(event) is True

    assert memory.edition_history(event) == [
        "WORLD-PULSE-EN-2026-08-30-1300"
    ]

    memory.close()


def test_run_edition_uses_supplied_memory():
    memory = EventMemory(":memory:")

    edition = run_edition(
        articles(),
        "2026-08-30",
        "20:00",
        event_memory=memory,
    )

    event = edition["top_story"]

    if event is None:
        event = (
            edition["main_stories"]
            + edition["briefs"]
        )[0]

    stored = memory.get(event)

    assert stored is not None
    assert stored["last_edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-2000"
    )

    memory.close()
