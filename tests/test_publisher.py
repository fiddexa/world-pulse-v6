from pipeline.publisher import (
    TELEGRAM,
    WEBSITE,
    MockPublisher,
    get_publisher,
)


def event():
    return {
        "publication": {
            "telegram": "Major earthquake strikes Nepal",
            "website": {
                "headline": "Major earthquake strikes Nepal",
            },
        }
    }


def test_mock_publisher_records_event():
    publisher = MockPublisher(TELEGRAM)

    result = publisher.publish(event())

    assert result["status"] == "SENT"
    assert result["channel"] == TELEGRAM
    assert len(publisher.published) == 1


def test_mock_publisher_keeps_event():
    item = event()
    publisher = MockPublisher(WEBSITE)

    publisher.publish(item)

    assert publisher.published[0] == item


def test_mock_publisher_does_not_modify_event():
    item = event()
    before = {
        "publication": dict(item["publication"])
    }

    publisher = MockPublisher(TELEGRAM)
    publisher.publish(item)

    assert item == before


def test_mock_publisher_rejects_invalid_event():
    publisher = MockPublisher(TELEGRAM)

    result = publisher.publish(None)

    assert result["status"] == "FAILED"


def test_get_telegram_publisher():
    publisher = get_publisher(
        TELEGRAM,
        mock=True,
    )

    assert isinstance(publisher, MockPublisher)
    assert publisher.channel == TELEGRAM


def test_get_website_publisher():
    publisher = get_publisher(
        WEBSITE,
        mock=True,
    )

    assert isinstance(publisher, MockPublisher)
    assert publisher.channel == WEBSITE


def test_unknown_channel_returns_none():
    assert get_publisher(
        "unknown",
        mock=True,
    ) is None


def test_mock_publisher_starts_empty():
    publisher = MockPublisher(TELEGRAM)

    assert publisher.published == []


def test_multiple_publications_are_recorded():
    publisher = MockPublisher(TELEGRAM)

    publisher.publish(event())
    publisher.publish(event())

    assert len(publisher.published) == 2
