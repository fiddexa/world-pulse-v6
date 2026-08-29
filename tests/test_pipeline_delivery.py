from pipeline.app import process_articles
from pipeline.delivery_executor import (
    BLOCKED,
    SKIPPED,
    execute_delivery,
)
from pipeline.delivery import TELEGRAM
from pipeline.delivery_log import DeliveryLog, SENT


def _articles():
    return [
        {
            "title": "Major earthquake strikes Nepal",
            "summary": (
                "A powerful earthquake hits Nepal. "
                "At least 100 people were killed."
            ),
            "published_at": "2026-08-29T10:00:00Z",
            "source": "Reuters",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
        {
            "title": "Strong earthquake hits Nepal",
            "summary": (
                "The earthquake causes widespread damage. "
                "100 people were killed."
            ),
            "published_at": "2026-08-29T10:20:00Z",
            "source": "BBC",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
    ]


def test_full_pipeline_produces_delivery_ready_event():
    events = process_articles(_articles())

    assert len(events) == 1

    event = events[0]

    assert "verification" in event
    assert "intelligence" in event
    assert "ranking_score" in event
    assert "editorial" in event
    assert "content" in event
    assert "publication" in event
    assert "delivery" in event

    assert (
        event["delivery"]["telegram"]["allowed"]
        is True
    )


def test_delivery_executor_can_send_processed_event():
    events = process_articles(_articles())
    event = events[0]

    log = DeliveryLog()

    result = execute_delivery(
        event,
        TELEGRAM,
        log,
    )

    assert result["status"] == SENT
    assert log.has_been_sent(
        event,
        TELEGRAM,
    )


def test_same_processed_event_is_not_sent_twice():
    events = process_articles(_articles())
    event = events[0]

    log = DeliveryLog()

    first = execute_delivery(
        event,
        TELEGRAM,
        log,
    )

    second = execute_delivery(
        event,
        TELEGRAM,
        log,
    )

    assert first["status"] == SENT
    assert second["status"] == SKIPPED


def test_blocked_editorial_event_is_not_sent():
    events = process_articles(_articles())
    event = events[0]

    event["editorial"]["decision"] = "REJECT"

    log = DeliveryLog()

    result = execute_delivery(
        event,
        TELEGRAM,
        log,
    )

    assert result["status"] == BLOCKED
    assert not log.has_been_sent(
        event,
        TELEGRAM,
    )
