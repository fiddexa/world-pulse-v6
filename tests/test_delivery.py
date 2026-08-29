from pipeline.delivery import (
    build_deliveries,
    build_delivery,
    delivery_policy,
)


def event():
    return {
        "editorial": {
            "decision": "STANDARD",
            "role": "BRIEF",
        },
        "publication": {
            "telegram": "Major earthquake strikes Nepal",
            "website": {
                "headline": "Major earthquake strikes Nepal",
            },
        },
    }


def test_standard_event_is_ready():
    result = delivery_policy(event())

    assert result["telegram"]["allowed"] is True
    assert result["website"]["allowed"] is True


def test_standard_event_has_ready_status():
    result = delivery_policy(event())

    assert result["telegram"]["status"] == "READY"
    assert result["website"]["status"] == "READY"


def test_reject_blocks_delivery():
    item = event()
    item["editorial"]["decision"] = "REJECT"

    result = delivery_policy(item)

    assert result["telegram"]["allowed"] is False
    assert result["website"]["allowed"] is False


def test_exclude_blocks_delivery():
    item = event()
    item["editorial"]["decision"] = "EXCLUDE"

    result = delivery_policy(item)

    assert result["telegram"]["allowed"] is False
    assert result["website"]["allowed"] is False


def test_hold_blocks_delivery():
    item = event()
    item["editorial"]["decision"] = "HOLD"

    result = delivery_policy(item)

    assert result["telegram"]["allowed"] is False
    assert result["website"]["allowed"] is False


def test_missing_telegram_content():
    item = event()
    item["publication"]["telegram"] = ""

    result = delivery_policy(item)

    assert result["telegram"]["allowed"] is False
    assert result["telegram"]["status"] == "NO_CONTENT"


def test_missing_website_content():
    item = event()
    item["publication"]["website"] = {}

    result = delivery_policy(item)

    assert result["website"]["allowed"] is False
    assert result["website"]["status"] == "NO_CONTENT"


def test_telegram_and_website_are_independent():
    item = event()
    item["publication"]["telegram"] = ""

    result = delivery_policy(item)

    assert result["telegram"]["allowed"] is False
    assert result["website"]["allowed"] is True


def test_invalid_event_is_safe():
    result = delivery_policy(None)

    assert result["telegram"]["allowed"] is False
    assert result["website"]["allowed"] is False


def test_build_delivery_preserves_event():
    original = event()

    result = build_delivery(original)

    assert result["editorial"] == original["editorial"]
    assert result["publication"] == original["publication"]
    assert "delivery" not in original


def test_build_deliveries_handles_multiple_events():
    result = build_deliveries([
        event(),
        event(),
    ])

    assert len(result) == 2
    assert all("delivery" in item for item in result)


def test_build_deliveries_invalid_input():
    assert build_deliveries(None) == []
