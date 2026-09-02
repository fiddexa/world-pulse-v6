from pipeline.edition_delivery_log import (
    SENT,
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)
from pipeline.edition_telegram_runner import (
    publish_edition_to_telegram,
    publish_editions_to_telegram,
)


class MockPublisher:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)

        return {
            "status": SENT,
            "channel": TELEGRAM,
            "message_id": 123,
        }


def edition():
    return {
        "edition_id": "20260829-2300-en",
        "edition_type": "WORLD_PULSE",
        "telegram": {
            "channel": TELEGRAM,
            "text": "AROUND THE MAIN\nTest edition",
        },
    }


def test_edition_is_sent():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition_to_telegram(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert result["status"] == SENT
    assert result["edition_id"] == "20260829-2300-en"
    assert result["message_id"] == 123
    assert len(publisher.published) == 1

    log.close()


def test_edition_is_not_sent_twice():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    first = publish_edition_to_telegram(
        edition(),
        log=log,
        publisher=publisher,
    )

    second = publish_edition_to_telegram(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert first["status"] == SENT
    assert second["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()


def test_different_editions_are_independent():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    first_edition = edition()

    second_edition = edition()
    second_edition["edition_id"] = (
        "20260830-0700-en"
    )

    first = publish_edition_to_telegram(
        first_edition,
        log=log,
        publisher=publisher,
    )

    second = publish_edition_to_telegram(
        second_edition,
        log=log,
        publisher=publisher,
    )

    assert first["status"] == SENT
    assert second["status"] == SENT
    assert len(publisher.published) == 2

    log.close()


def test_invalid_edition_is_rejected():
    result = publish_edition_to_telegram(None)

    assert result["status"] == "FAILED"
    assert result["channel"] == TELEGRAM


def test_missing_edition_id_is_rejected():
    item = edition()
    item["edition_id"] = ""

    result = publish_edition_to_telegram(item)

    assert result["status"] == "FAILED"
    assert result["reason"] == "MISSING_EDITION_ID"


def test_missing_telegram_content_is_rejected():
    item = edition()
    item["telegram"]["text"] = ""

    result = publish_edition_to_telegram(item)

    assert result["status"] == "FAILED"
    assert result["reason"] == "NO_CONTENT"


def test_batch_uses_same_log():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_editions_to_telegram(
        [edition(), edition()],
        log=log,
        publisher=publisher,
    )

    assert result[0]["status"] == SENT
    assert result[1]["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()


def test_batch_invalid_input_is_safe():
    assert publish_editions_to_telegram(None) == []
