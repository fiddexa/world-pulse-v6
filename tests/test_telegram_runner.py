from pipeline.delivery_log import TELEGRAM, DeliveryLog
from pipeline.telegram_runner import (
    publish_event_to_telegram,
    publish_events_to_telegram,
)
from pipeline.publisher import MockPublisher
from pipeline.sqlite_delivery_log import SQLiteDeliveryLog


def event():
    return {
        "editorial": {
            "decision": "STANDARD",
        },
        "publication": {
            "telegram": "WORLD PULSE TEST",
            "website": {
                "headline": "WORLD PULSE TEST",
            },
        },
        "content": {
            "headline": "WORLD PULSE TEST",
            "published_at": "2026-08-29T23:00:00Z",
            "sources": ["test"],
            "affected_areas": ["test"],
        },
    }


def test_invalid_event_is_rejected():
    result = publish_event_to_telegram(None)

    assert result["status"] == "FAILED"
    assert result["channel"] == TELEGRAM


def test_runner_can_use_explicit_log(monkeypatch):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    log = DeliveryLog()

    result = publish_event_to_telegram(
        event(),
        log=log,
    )

    assert result["status"] == "SENT"
    assert len(publisher.published) == 1
    assert log.has_been_sent(
        event(),
        TELEGRAM,
    )


def test_runner_preserves_idempotency(monkeypatch):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    log = DeliveryLog()

    first = publish_event_to_telegram(
        event(),
        log=log,
    )

    second = publish_event_to_telegram(
        event(),
        log=log,
    )

    assert first["status"] == "SENT"
    assert second["status"] == "SKIPPED"
    assert len(publisher.published) == 1


def test_runner_handles_batch(monkeypatch):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    log = DeliveryLog()

    results = publish_events_to_telegram(
        [
            event(),
            {
                "editorial": {
                    "decision": "STANDARD",
                },
                "publication": {
                    "telegram": "SECOND TEST",
                    "website": {
                        "headline": "SECOND TEST",
                    },
                },
                "content": {
                    "headline": "SECOND TEST",
                    "published_at": "2026-08-29T23:01:00Z",
                    "sources": ["test-2"],
                    "affected_areas": ["test-2"],
                },
            },
        ],
        log=log,
    )

    assert len(results) == 2
    assert results[0]["status"] == "SENT"
    assert results[1]["status"] == "SENT"
    assert len(publisher.published) == 2


def test_batch_reuses_same_log(
    monkeypatch,
    tmp_path,
):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    log = SQLiteDeliveryLog(
        tmp_path / "telegram.sqlite3"
    )

    item = event()

    results = publish_events_to_telegram(
        [item, item],
        log=log,
    )

    assert results[0]["status"] == "SENT"
    assert results[1]["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()


def test_non_list_batch_is_safe():
    assert publish_events_to_telegram(None) == []


def test_runner_does_not_modify_event(monkeypatch):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    item = event()
    before = {
        "editorial": dict(item["editorial"]),
        "publication": dict(item["publication"]),
        "content": dict(item["content"]),
    }

    publish_event_to_telegram(item)

    assert item == before


def test_runner_is_explicitly_telegram_only(monkeypatch):
    from pipeline import telegram_runner

    publisher = MockPublisher(TELEGRAM)

    monkeypatch.setattr(
        telegram_runner,
        "get_telegram_publisher",
        lambda: publisher,
    )

    result = publish_event_to_telegram(event())

    assert result["channel"] == TELEGRAM
