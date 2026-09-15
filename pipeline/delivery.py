"""
AROUND THE MAIN v6 - Delivery Policy Layer

Determines whether prepared publication content is ready for delivery.

This layer:
- does not publish externally;
- does not modify editorial decisions;
- does not change verification;
- does not change intelligence;
- does not invent content.
"""


TELEGRAM = "telegram"
WEBSITE = "website"


BLOCKED_DECISIONS = {
    "REJECT",
    "EXCLUDE",
    "HOLD",
}


def _safe_text(value):
    if value is None:
        return ""

    return str(value).strip()


def _editorial(event):
    if not isinstance(event, dict):
        return {}

    value = event.get("editorial")

    if isinstance(value, dict):
        return value

    return {}


def _publication(event):
    if not isinstance(event, dict):
        return {}

    value = event.get("publication")

    if isinstance(value, dict):
        return value

    return {}


def _decision(event):
    editorial = _editorial(event)

    return _safe_text(
        editorial.get("decision", "STANDARD")
    ).upper()


def _has_telegram(event):
    publication = _publication(event)

    return bool(
        _safe_text(
            publication.get("telegram")
        )
    )


def _has_website(event):
    publication = _publication(event)

    website = publication.get("website")

    return isinstance(website, dict) and bool(
        _safe_text(website.get("headline"))
    )


def delivery_policy(event):
    """
    Return delivery readiness without modifying the event.
    """

    if not isinstance(event, dict):
        return {
            "telegram": {
                "allowed": False,
                "status": "INVALID_EVENT",
            },
            "website": {
                "allowed": False,
                "status": "INVALID_EVENT",
            },
        }

    decision = _decision(event)

    if decision in BLOCKED_DECISIONS:
        status = "BLOCKED"

        return {
            "telegram": {
                "allowed": False,
                "status": status,
            },
            "website": {
                "allowed": False,
                "status": status,
            },
        }

    telegram_ready = _has_telegram(event)
    website_ready = _has_website(event)

    return {
        "telegram": {
            "allowed": telegram_ready,
            "status": (
                "READY"
                if telegram_ready
                else "NO_CONTENT"
            ),
        },
        "website": {
            "allowed": website_ready,
            "status": (
                "READY"
                if website_ready
                else "NO_CONTENT"
            ),
        },
    }


def build_delivery(event):
    """
    Add delivery policy metadata without modifying the original event.
    """

    if not isinstance(event, dict):
        return {}

    result = dict(event)

    result["delivery"] = delivery_policy(event)

    return result


def build_deliveries(events):
    """
    Build delivery policies for multiple events.
    """

    if not isinstance(events, list):
        return []

    return [
        build_delivery(event)
        for event in events
        if isinstance(event, dict)
    ]
