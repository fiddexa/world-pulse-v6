from pipeline.sqlite_delivery_log import SQLiteDeliveryLog
from pipeline.delivery_log import (
    FAILED,
    SENT,
    TELEGRAM,
    WEBSITE,
)


def event():
    return {
        "content": {
            "headline": "Major earthquake strikes Nepal",
            "published_at": "2026-08-29T10:00:00Z",
            "sources": ["bbc", "reuters"],
            "affected_areas": ["nepal"],
        },
        "publication": {
            "telegram": "Major earthquake strikes Nepal",
            "website": {
                "headline": "Major earthquake strikes Nepal",
            },
        },
    }


def test_sqlite_log_starts_empty(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    log = SQLiteDeliveryLog(db_path)

    assert log.has_been_sent(
        event(),
        TELEGRAM,
    ) is False

    log.close()


def test_record_sent_is_persistent(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    first_log = SQLiteDeliveryLog(db_path)

    assert first_log.record_sent(
        event(),
        TELEGRAM,
    ) is True

    assert first_log.has_been_sent(
        event(),
        TELEGRAM,
    ) is True

    first_log.close()

    second_log = SQLiteDeliveryLog(db_path)

    assert second_log.has_been_sent(
        event(),
        TELEGRAM,
    ) is True

    assert second_log.status(
        event(),
        TELEGRAM,
    ) == SENT

    second_log.close()


def test_failed_status_is_persistent(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    first_log = SQLiteDeliveryLog(db_path)

    assert first_log.record_failed(
        event(),
        WEBSITE,
    ) is True

    first_log.close()

    second_log = SQLiteDeliveryLog(db_path)

    assert second_log.status(
        event(),
        WEBSITE,
    ) == FAILED

    assert second_log.has_been_sent(
        event(),
        WEBSITE,
    ) is False

    second_log.close()


def test_channels_are_independent(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    log = SQLiteDeliveryLog(db_path)

    log.record_sent(
        event(),
        TELEGRAM,
    )

    assert log.has_been_sent(
        event(),
        TELEGRAM,
    ) is True

    assert log.has_been_sent(
        event(),
        WEBSITE,
    ) is False

    log.close()


def test_failed_can_become_sent(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    log = SQLiteDeliveryLog(db_path)

    log.record_failed(
        event(),
        TELEGRAM,
    )

    assert log.status(
        event(),
        TELEGRAM,
    ) == FAILED

    log.record_sent(
        event(),
        TELEGRAM,
    )

    assert log.status(
        event(),
        TELEGRAM,
    ) == SENT

    assert log.has_been_sent(
        event(),
        TELEGRAM,
    ) is True

    log.close()


def test_clear_removes_persistent_records(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    first_log = SQLiteDeliveryLog(db_path)

    first_log.record_sent(
        event(),
        TELEGRAM,
    )

    first_log.clear()

    assert first_log.status(
        event(),
        TELEGRAM,
    ) is None

    first_log.close()

    second_log = SQLiteDeliveryLog(db_path)

    assert second_log.status(
        event(),
        TELEGRAM,
    ) is None

    second_log.close()


def test_invalid_event_does_not_create_record(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    log = SQLiteDeliveryLog(db_path)

    assert log.record_sent(
        None,
        TELEGRAM,
    ) is False

    assert log.status(
        None,
        TELEGRAM,
    ) is None

    log.close()


def test_invalid_channel_does_not_create_record(tmp_path):
    db_path = tmp_path / "delivery.sqlite3"

    log = SQLiteDeliveryLog(db_path)

    assert log.record_sent(
        event(),
        "unknown",
    ) is False

    assert log.status(
        event(),
        "unknown",
    ) is None

    log.close()


def test_executor_with_sqlite_log_is_persistent(tmp_path):
    from pipeline.delivery_executor import execute_delivery

    db_path = tmp_path / "delivery.sqlite3"

    first_log = SQLiteDeliveryLog(db_path)

    first = execute_delivery(
        event(),
        TELEGRAM,
        first_log,
    )

    assert first["status"] == SENT

    first_log.close()

    second_log = SQLiteDeliveryLog(db_path)

    second = execute_delivery(
        event(),
        TELEGRAM,
        second_log,
    )

    assert second["status"] == "SKIPPED"

    second_log.close()
