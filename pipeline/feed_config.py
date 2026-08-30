"""
WORLD PULSE v6 - Feed Configuration

Production RSS/Atom feed configuration.

This module contains technical feed endpoints and their
operational requirements.

Source reputation, tier, independence and category metadata
remain in pipeline.sources.

Only verified public endpoints should be placed in
FEED_REGISTRY.

Sources requiring authentication or commercial syndication
must not be represented as public RSS feeds.
"""

from copy import deepcopy


FEED_REGISTRY = {
    # Public / verified RSS sources.
    "un": [
        {
            "url": (
                "https://www.un.org/en/ga/rss/"
                "news.xml"
            ),
            "source": "United Nations",
            "type": "rss",
            "requires_auth": False,
        },
    ],

    # IMF confirms official RSS availability.
    # The exact production news feed endpoint should be
    # verified before activation.
    "imf": [],

    # Reuters RSS delivery is not treated as a public
    # unauthenticated feed.
    "reuters": [],

    # AP distribution is not treated as a public
    # unauthenticated feed.
    "associated_press": [],

    # BBC Information Syndication API requires an API key
    # and an established syndication relationship.
    "bbc": [],

    # AFP distribution requires an appropriate commercial/API
    # arrangement.
    "afp": [],

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
    Return source identifiers that currently have
    production feed endpoints.
    """

    return [
        source
        for source, feeds in FEED_REGISTRY.items()
        if feeds
    ]


def all_sources():
    """
    Return all supported source identifiers.

    This includes sources that currently have no public
    production feed configured.
    """

    return list(
        FEED_REGISTRY.keys()
    )


def source_requires_auth(
    source,
):
    """
    Return True when at least one configured feed for the
    source requires authentication.
    """

    feeds = get_feeds(source)

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
