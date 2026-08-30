from pipeline.event_memory import EventMemory
from pipeline.delivery_log import event_fingerprint


def event():
    return {
        "content": {
            "headline": "Major earthquake strikes Nepal",
            "published_at": "2026-08-29T10:00:00Z",
            "sources": ["bbc", "reuters"],
            "affected_areas": ["nepal"],
        }
    }


def different_event():
    return {
        "content": {
            "headline": "Major earthquake strikes India",
            "published_at": "2026-08-29T11:00:00Z",
            "sources": ["bbc"],
            "affected_areas": ["india"],
        }
    }


def test_memory_starts_empty(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    assert memory.has_seen(event()) is False
    assert memory.get(event()) is None

    memory.close()


def test_remember_marks_event_as_seen(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    assert memory.remember(event()) is True
    assert memory.has_seen(event()) is True

    memory.close()


def test_remember_uses_existing_event_fingerprint(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())

    stored = memory.get(event())

    assert stored["fingerprint"] == event_fingerprint(
        event()
    )

    memory.close()


def test_new_event_has_occurrence_count_one(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())

    stored = memory.get(event())

    assert stored["occurrence_count"] == 1

    memory.close()


def test_repeated_event_increments_occurrence_count(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())
    memory.remember(event())

    stored = memory.get(event())

    assert stored["occurrence_count"] == 2

    memory.close()


def test_different_events_are_stored_independently(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())
    memory.remember(different_event())

    assert memory.has_seen(event()) is True
    assert memory.has_seen(different_event()) is True

    first = memory.get(event())
    second = memory.get(different_event())

    assert first["fingerprint"] != second["fingerprint"]
    assert first["occurrence_count"] == 1
    assert second["occurrence_count"] == 1

    memory.close()


def test_edition_id_is_stored(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(
        event(),
        edition_id="WORLD-PULSE-EN-2026-08-30-0700",
    )

    stored = memory.get(event())

    assert stored["last_edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-0700"
    )

    memory.close()


def test_new_edition_id_replaces_previous_edition_id(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(
        event(),
        edition_id="WORLD-PULSE-EN-2026-08-30-0700",
    )

    memory.remember(
        event(),
        edition_id="WORLD-PULSE-EN-2026-08-30-1300",
    )

    stored = memory.get(event())

    assert stored["last_edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )
    assert stored["occurrence_count"] == 2

    memory.close()


def test_memory_survives_process_restart(tmp_path):
    db_path = tmp_path / "events.sqlite3"

    first_memory = EventMemory(db_path)

    first_memory.remember(
        event(),
        edition_id="WORLD-PULSE-EN-2026-08-30-0700",
    )

    first_memory.close()

    second_memory = EventMemory(db_path)

    assert second_memory.has_seen(event()) is True

    stored = second_memory.get(event())

    assert stored["occurrence_count"] == 1
    assert stored["last_edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-0700"
    )

    second_memory.close()


def test_forget_removes_event(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())

    assert memory.forget(event()) is True
    assert memory.has_seen(event()) is False
    assert memory.get(event()) is None

    memory.close()


def test_forget_unknown_event_returns_false(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    assert memory.forget(event()) is False

    memory.close()


def test_clear_removes_all_events(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    memory.remember(event())
    memory.remember(different_event())

    memory.clear()

    assert memory.has_seen(event()) is False
    assert memory.has_seen(different_event()) is False

    memory.close()


def test_invalid_event_is_not_stored(tmp_path):
    memory = EventMemory(
        tmp_path / "events.sqlite3"
    )

    assert memory.remember(None) is False
    assert memory.has_seen(None) is False
    assert memory.get(None) is None
    assert memory.forget(None) is False

    memory.close()
