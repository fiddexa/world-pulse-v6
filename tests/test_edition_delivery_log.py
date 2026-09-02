from pipeline.edition_delivery_log import (
    FAILED,
    SENT,
    TELEGRAM,
    SQLiteEditionDeliveryLog,
    edition_fingerprint,
)


def edition():
    return {
        "edition_id": "20260829-2300-en",
        "edition_type": "WORLD_PULSE",
        "telegram": {
            "channel": "telegram",
            "text": "AROUND THE MAIN\nTest edition",
        },
    }


def test_fingerprint_is_deterministic():
    first = edition_fingerprint(edition())
    second = edition_fingerprint(edition())

    assert first
    assert first == second


def test_fingerprint_uses_edition_id():
    first = edition()

    second = edition()
    second["telegram"]["text"] = "DIFFERENT TEXT"

    assert edition_fingerprint(first) == (
        edition_fingerprint(second)
    )


def test_unknown_edition_has_empty_fingerprint():
    assert edition_fingerprint(None) == ""


def test_log_starts_empty(tmp_path):
    log = SQLiteEditionDeliveryLog(
        tmp_path / "edition.sqlite3"
    )

    assert not log.has_been_sent(
        edition(),
        TELEGRAM,
    )

    log.close()


def test_record_sent(tmp_path):
    log = SQLiteEditionDeliveryLog(
        tmp_path / "edition.sqlite3"
    )

    assert log.record_sent(
        edition(),
        TELEGRAM,
    )

    assert log.has_been_sent(
        edition(),
        TELEGRAM,
    )

    assert log.status(
        edition(),
        TELEGRAM,
    ) == SENT

    log.close()


def test_record_failed(tmp_path):
    log = SQLiteEditionDeliveryLog(
        tmp_path / "edition.sqlite3"
    )

    assert log.record_failed(
        edition(),
        TELEGRAM,
    )

    assert log.status(
        edition(),
        TELEGRAM,
    ) == FAILED

    assert not log.has_been_sent(
        edition(),
        TELEGRAM,
    )

    log.close()


def test_failed_can_become_sent(tmp_path):
    log = SQLiteEditionDeliveryLog(
        tmp_path / "edition.sqlite3"
    )

    log.record_failed(
        edition(),
        TELEGRAM,
    )

    log.record_sent(
        edition(),
        TELEGRAM,
    )

    assert log.status(
        edition(),
        TELEGRAM,
    ) == SENT

    log.close()


def test_state_survives_restart(tmp_path):
    path = tmp_path / "edition.sqlite3"

    first = SQLiteEditionDeliveryLog(path)

    first.record_sent(
        edition(),
        TELEGRAM,
    )

    first.close()

    second = SQLiteEditionDeliveryLog(path)

    assert second.has_been_sent(
        edition(),
        TELEGRAM,
    )

    second.close()


def test_invalid_channel_is_rejected(tmp_path):
    log = SQLiteEditionDeliveryLog(
        tmp_path / "edition.sqlite3"
    )

    assert not log.record_sent(
        edition(),
        "website",
    )

    assert log.status(
        edition(),
        "website",
    ) is None

    log.close()
