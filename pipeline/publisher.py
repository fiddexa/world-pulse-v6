"""
AROUND THE MAIN v6 - Publisher Interface

Defines a small publisher abstraction for external channels.

The default implementation is a mock publisher for safe testing.
No external network calls are made by this module.
"""

from typing import Any


TELEGRAM = "telegram"
WEBSITE = "website"


class Publisher:
    """Base publisher interface."""

    channel = None

    def publish(self, event: dict) -> dict:
        raise NotImplementedError


class MockPublisher(Publisher):
    """
    Test publisher.

    Records publication attempts without making external calls.
    """

    def __init__(self, channel: str):
        self.channel = channel
        self.published = []

    def publish(self, event: dict) -> dict:
        if not isinstance(event, dict):
            return {
                "status": "FAILED",
                "channel": self.channel,
            }

        self.published.append(event)

        return {
            "status": "SENT",
            "channel": self.channel,
        }


def get_publisher(channel: Any, *, mock: bool = True):
    """
    Return a publisher for the requested channel.

    Real external publishers will be added later.
    """

    if channel not in {
        TELEGRAM,
        WEBSITE,
    }:
        return None

    if mock:
        return MockPublisher(channel)

    return None
