"""
WORLD PULSE v6 - Feed Configuration

Production RSS/Atom feed configuration.

This module contains technical feed endpoints only.

Source reputation, tier, independence and category metadata
remain in pipeline.sources.

Only verified public feeds are enabled.

Sources without a verified production feed remain empty.
"""

from copy import deepcopy


FEED_REGISTRY = {
    "reuters": [],

    "associated_press": [],

    "bbc": [],

    "afp": [],

    "un": [
        {
            "url": (
                "https://news.un.org/"
                "feed/subscribe/en/news/all/rss.xml"
            ),
            "source": "UN",
            "name": "UN News",
            "type": "rss",
            "requires_auth": False,
            "category": "world",
        },
    ],

    "imf": [],

    "world_bank": [],

    "who": [],

    "iea": [],

    "opec": [],
}


def all_sources():
    """
    Return all registered source identifiers.

    This includes sources that currently have no verified
    production feed.
    """

    return list(
        FEED_REGISTRY.keys()
    )


def get_feeds(source=None):
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
    Return source identifiers that currently have
    configured production feeds.
    """

    return [
        source
        for source, feeds in FEED_REGISTRY.items()
        if feeds
    ]


def source_requires_auth(source):
    """
    Return True when at least one configured feed for the
    source requires authentication.

    Unknown sources and sources without configured feeds
    conservatively return False.
    """

    feeds = get_feeds(source)

    if not feeds:
        return False

    return any(
        bool(
            feed.get(
                "requires_auth",
                False,
            )
        )
        for feed in feeds
        if isinstance(feed, dict)
    )
