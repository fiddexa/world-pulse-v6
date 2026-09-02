from pipeline.edition_memory import (
    COMPLETED,
    FAILED,
    RUNNING,
    EditionMemory,
)


EDITION_ID = "AROUND-THE-MAIN-EN-2026-08-30-1300"


def test_memory_starts_empty(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    assert memory.status(EDITION_ID) is None
    assert memory.exists(EDITION_ID) is False
    assert memory.can_start(EDITION_ID) is True

    memory.close()


def test_start_creates_running_edition(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    assert memory.start(EDITION_ID) is True
    assert memory.status(EDITION_ID) == RUNNING
    assert memory.exists(EDITION_ID) is True
    assert memory.can_start(EDITION_ID) is False

    memory.close()


def test_same_edition_cannot_start_twice(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    assert memory.start(EDITION_ID) is True
    assert memory.start(EDITION_ID) is False
    assert memory.status(EDITION_ID) == RUNNING

    memory.close()


def test_completed_edition_cannot_start_again(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    memory.start(EDITION_ID)

    assert memory.complete(EDITION_ID) is True
    assert memory.status(EDITION_ID) == COMPLETED

    assert memory.start(EDITION_ID) is False

    memory.close()


def test_failed_edition_can_be_recorded(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    memory.start(EDITION_ID)

    assert memory.fail(EDITION_ID) is True
    assert memory.status(EDITION_ID) == FAILED

    memory.close()


def test_complete_requires_existing_edition(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    assert memory.complete(EDITION_ID) is False
    assert memory.status(EDITION_ID) is None

    memory.close()


def test_fail_requires_existing_edition(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    assert memory.fail(EDITION_ID) is False
    assert memory.status(EDITION_ID) is None

    memory.close()


def test_clear_removes_editions(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    memory.start(EDITION_ID)

    assert memory.exists(EDITION_ID) is True

    memory.clear()

    assert memory.exists(EDITION_ID) is False
    assert memory.status(EDITION_ID) is None

    memory.close()


def test_memory_survives_process_restart(tmp_path):
    db_path = tmp_path / "editions.sqlite3"

    first = EditionMemory(db_path)

    assert first.start(EDITION_ID) is True
    assert first.complete(EDITION_ID) is True

    first.close()

    second = EditionMemory(db_path)

    assert second.exists(EDITION_ID) is True
    assert second.status(EDITION_ID) == COMPLETED

    second.close()


def test_different_editions_are_independent(tmp_path):
    memory = EditionMemory(
        tmp_path / "editions.sqlite3"
    )

    first = "AROUND-THE-MAIN-EN-2026-08-30-0700"
    second = "AROUND-THE-MAIN-EN-2026-08-30-1300"

    assert memory.start(first) is True
    assert memory.start(second) is True

    assert memory.status(first) == RUNNING
    assert memory.status(second) == RUNNING

    memory.complete(first)

    assert memory.status(first) == COMPLETED
    assert memory.status(second) == RUNNING

    memory.close()
