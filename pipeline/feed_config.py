"""
WORLD PULSE v6 - Feed Configuration

Production RSS/Atom feed configuration.

This module contains technical feed endpoints only.
Source reputation, tier, independence and category metadata
remain in pipeline.sources.
"""

from copy import deepcopy


FEED_REGISTRY = {
    "reuters": [],
    "associated_press": [],
    "bbc": [],
    "afp": [],
    "un": [],
    "imf": [],
    "world_bank": [],
    "who": [],
    "iea": [],
    "opec": [],
}


def get_feeds(
    source=None,
):
    """
    Return configured production feeds.

    When source is omitted, return feeds for all configured
    sources.

    Returned records are defensive copies.
    """

    if source is not None:
        key = str(source).strip().lower()

        feeds = FEED_REGISTRY.get(
            key,
            [],
        )

        return deepcopy(feeds)

    result = []

    for feeds in FEED_REGISTRY.values():
        result.extend(
            deepcopy(feeds)
        )

    return result


def configured_sources():
    """
    Return source identifiers that have feed configuration.
    """

    return [
        source
        for source, feeds in FEED_REGISTRY.items()
        if feeds
    ]
