from pipeline.delivery import TELEGRAM, WEBSITE
from pipeline.delivery_executor import (
    BLOCKED,
    READY,
    SKIPPED,
    execute_delivery,
    execute_event,
    execution_status,
)
from pipeline.delivery_log import (
    DeliveryLog,
    SENT,
)


def event():
    return {
        "editorial": {
            "decision": "STANDARD",
        },
        "publication": {
            "telegram": "Major earthquake strikes Nepal",
            "website": {
                "headline": "Major earthquake strikes Nepal",
            },
        },
    }


def test_ready_event_can_be_executed():
    log = DeliveryLog()

    assert execution_status(
        event(),
        TELEGRAM,
        log,
    ) == READY


def test_successful_execution_marks_sent():
    log = DeliveryLog()

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
    )

    assert result["status"] == SENT
    assert log.has_been_sent(
        event(),
        TELEGRAM,
    )


def test_duplicate_execution_is_skipped():
    log = DeliveryLog()

    execute_delivery(
        event(),
        TELEGRAM,
        log,
    )

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
    )

    assert result["status"] == SKIPPED


def test_blocked_event_cannot_execute():
    item = event()
    item["editorial"]["decision"] = "REJECT"

    log = DeliveryLog()

    assert execution_status(
        item,
        TELEGRAM,
        log,
    ) == BLOCKED

    result = execute_delivery(
        item,
        TELEGRAM,
        log,
    )

    assert result["status"] == BLOCKED


def test_failed_execution_is_recorded():
    log = DeliveryLog()

    result = execute_delivery(
        event(),
        WEBSITE,
        log,
        success=False,
    )

    assert result["status"] == "FAILED"
    assert log.status(
        event(),
        WEBSITE,
    ) == "FAILED"


def test_failed_execution_can_be_retried():
    log = DeliveryLog()

    execute_delivery(
        event(),
        WEBSITE,
        log,
        success=False,
    )

    result = execute_delivery(
        event(),
        WEBSITE,
        log,
        success=True,
    )

    assert result["status"] == SENT


def test_channels_are_independent():
    log = DeliveryLog()

    execute_delivery(
        event(),
        TELEGRAM,
        log,
    )

    result = execute_delivery(
        event(),
        WEBSITE,
        log,
    )

    assert result["status"] == SENT


def test_execute_event_handles_both_channels():
    log = DeliveryLog()

    result = execute_event(
        event(),
        log,
    )

    assert result[TELEGRAM]["status"] == SENT
    assert result[WEBSITE]["status"] == SENT


def test_execute_event_can_limit_channels():
    log = DeliveryLog()

    result = execute_event(
        event(),
        log,
        channels=[TELEGRAM],
    )

    assert TELEGRAM in result
    assert WEBSITE not in result


def test_invalid_channels_are_not_executed():
    log = DeliveryLog()

    result = execute_event(
        event(),
        log,
        channels="telegram",
    )

    assert result == {}


def test_original_event_is_not_modified():
    original = event()

    before = {
        "editorial": dict(original["editorial"]),
        "publication": dict(original["publication"]),
    }

    log = DeliveryLog()

    execute_event(original, log)

    assert original == before


def test_executor_uses_publisher():
    from pipeline.publisher import MockPublisher

    log = DeliveryLog()
    publisher = MockPublisher(TELEGRAM)

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
        publisher=publisher,
    )

    assert result["status"] == SENT
    assert len(publisher.published) == 1
    assert log.has_been_sent(
        event(),
        TELEGRAM,
    )


def test_executor_skips_before_publisher():
    from pipeline.publisher import MockPublisher

    log = DeliveryLog()
    publisher = MockPublisher(TELEGRAM)

    execute_delivery(
        event(),
        TELEGRAM,
        log,
        publisher=publisher,
    )

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
        publisher=publisher,
    )

    assert result["status"] == SKIPPED
    assert len(publisher.published) == 1


def test_executor_records_publisher_failure():
    class FailedPublisher:
        def publish(self, event):
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "TEST_FAILURE",
            }

    log = DeliveryLog()

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
        publisher=FailedPublisher(),
    )

    assert result["status"] == "FAILED"
    assert log.status(
        event(),
        TELEGRAM,
    ) == "FAILED"


def test_executor_can_use_telegram_publisher():
    from pipeline.telegram_publisher import TelegramPublisher

    def transport(**kwargs):
        return {
            "ok": True,
            "result": {
                "message_id": 123,
            },
        }

    publisher = TelegramPublisher(
        token="test-token",
        chat_id="-100123",
        transport=transport,
    )

    log = DeliveryLog()

    result = execute_delivery(
        event(),
        TELEGRAM,
        log,
        publisher=publisher,
    )

    assert result["status"] == SENT
    assert result["message_id"] == 123
    assert log.has_been_sent(
        event(),
        TELEGRAM,
    )


def test_execute_event_accepts_publishers():
    from pipeline.publisher import MockPublisher

    log = DeliveryLog()
    telegram = MockPublisher(TELEGRAM)

    result = execute_event(
        event(),
        log,
        channels=[TELEGRAM],
        publishers={
            TELEGRAM: telegram,
        },
    )

    assert result[TELEGRAM]["status"] == SENT
    assert len(telegram.published) == 1
