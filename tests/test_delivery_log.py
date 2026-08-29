from pipeline.delivery_log import (
    DeliveryLog,
    FAILED,
    READY,
    SENT,
    TELEGRAM,
    WEBSITE,
    create_delivery_record,
    event_fingerprint,
)


def event():
    return {
        "content": {
            "headline": "Major earthquake strikes Nepal",
            "published_at": "2026-08-29T10:00:00Z",
            "sources": ["bbc", "reuters"],
            "affected_areas": ["nepal"],
        }
    }


def test_fingerprint_is_deterministic():
    assert event_fingerprint(event()) == event_fingerprint(event())


def test_fingerprint_is_not_empty_for_valid_event():
    assert event_fingerprint(event())


def test_different_events_have_different_fingerprints():
    first = event()

    second = event()
    second["content"]["headline"] = "Different event"

    assert event_fingerprint(first) != event_fingerprint(second)


def test_create_delivery_record_is_ready():
    result = create_delivery_record(
        event(),
        TELEGRAM,
    )

    assert result["status"] == READY
    assert result["channel"] == TELEGRAM
    assert result["fingerprint"]


def test_invalid_channel_creates_failed_record():
    result = create_delivery_record(
        event(),
        "unknown",
    )

    assert result["status"] == FAILED


def test_invalid_event_creates_failed_record():
    result = create_delivery_record(
        None,
        TELEGRAM,
    )

    assert result["status"] == FAILED


def test_delivery_log_starts_empty():
    log = DeliveryLog()

    assert log.has_been_sent(
        event(),
        TELEGRAM,
    ) is False


def test_record_sent_marks_event_as_sent():
    log = DeliveryLog()

    assert log.record_sent(
        event(),
        TELEGRAM,
    ) is True

    assert log.has_been_sent(
        event(),
        TELEGRAM,
    ) is True


def test_channels_are_independent():
    log = DeliveryLog()

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


def test_failed_status_is_recorded():
    log = DeliveryLog()

    assert log.record_failed(
        event(),
        WEBSITE,
    ) is True

    assert log.status(
        event(),
        WEBSITE,
    ) == FAILED

    assert log.has_been_sent(
        event(),
        WEBSITE,
    ) is False


def test_status_returns_sent():
    log = DeliveryLog()

    log.record_sent(
        event(),
        WEBSITE,
    )

    assert log.status(
        event(),
        WEBSITE,
    ) == SENT


def test_clear_removes_records():
    log = DeliveryLog()

    log.record_sent(
        event(),
        TELEGRAM,
    )

    log.clear()

    assert log.status(
        event(),
        TELEGRAM,
    ) is None


def test_delivery_log_does_not_modify_event():
    original = event()
    before = {
        "content": dict(original["content"])
    }

    log = DeliveryLog()
    log.record_sent(
        original,
        TELEGRAM,
    )

    assert original == before
